"""
pip install xlwt xmindparser
"""
from io import BytesIO
from typing import Any, Optional

from pydantic.dataclasses import dataclass, Field
from xlwt import Alignment, Column, Font, Row, Workbook, Worksheet, XFStyle
from xmindparser import xmind_to_dict


@dataclass
class Topic:
    title: str
    topics: list["Topic"] = Field(default_factory=list)


@dataclass
class Canvas:
    title: str
    topic: Topic
    structure: str


@dataclass
class XmindInfo:
    root: list[Canvas]


@dataclass
class CellData:
    is_combo: bool = False
    is_none: bool = False
    data: Any = ""
    set_colour: bool = False
    colour_index: int = 0x7FFF

    def __repr__(self) -> str:
        return f"CellData(is_combo={self.is_combo}, is_none={self.is_none}, data={self.data})"

    def __str__(self) -> str:
        return str(self.data)


class XmindUtils:
    def __init__(self, xmid_info: XmindInfo):
        self.topic = xmid_info.root[0].topic
        self.data: list[list[str]] = []

    @staticmethod
    def get_xmind(filename: str) -> XmindInfo:
        data = xmind_to_dict(filename)
        return XmindInfo(root=data)

    def _build_data(self, toppic: Topic, data: list[str]) -> None:
        if not toppic.topics:
            self.data.append(data + [toppic.title])
            return

        for tic in toppic.topics:
            self._build_data(tic, data + [toppic.title])

    def build(self) -> list[list[str]]:
        for toppic in self.topic.topics:
            self._build_data(toppic, [self.topic.title])
        return self.data


class ExcelUtils:
    @staticmethod
    def new_workbook() -> Workbook:
        return Workbook(style_compression=2)

    @staticmethod
    def calc_cell_width(cell: Any) -> int:
        if not isinstance(cell, str):
            cell = str(cell)
        return min(65535, max((len(val.encode("gb18030")) + 2) * 256 for val in cell.split("\n")))

    @staticmethod
    def set_row_height(sheet: Worksheet, row: int, height: int) -> None:
        curr_row: Row = sheet.row(row)
        curr_row.height_mismatch = 1
        curr_row.height = 0x00FF * height

    @staticmethod
    def get_cell_style(cell: Any) -> str:
        if isinstance(cell, float):
            return "0.00"
        if isinstance(cell, int):
            return "0"
        return "@"

    @staticmethod
    def gen_style() -> XFStyle:
        style = XFStyle()
        al = Alignment()
        al.wrap = Alignment.WRAP_AT_RIGHT  # 设置自动换行
        al.vert = Alignment.VERT_CENTER  # 设置垂直居中
        style.alignment = al
        return style

    @staticmethod
    def gen_merge_style() -> XFStyle:
        mg_al = Alignment()
        mg_al.horz = Alignment.HORZ_LEFT  # 设置左对齐
        mg_al.vert = Alignment.VERT_CENTER  # 设置垂直居中
        mg_al.wrap = Alignment.WRAP_AT_RIGHT  # 设置自动换行
        mg_style = XFStyle()
        mg_style.alignment = mg_al
        return mg_style

    @staticmethod
    def write_data(
        sheet: Worksheet,
        excel_data: list[list[str]],
        *,
        offset: int = 0,
        col_styles: Optional[list[Optional[XFStyle]]] = None,
        adaptive_col_width: bool = False,
        adaptive_row_height: bool = False,
    ) -> list[int]:
        style = ExcelUtils.gen_style()
        col_widths = [0] * len(excel_data[0]) if excel_data else []
        max_row = 1
        for row, row_data in enumerate(excel_data):
            for col, cell in enumerate(row_data):
                if col_styles and col < len(col_styles) and col_styles[col]:
                    style = col_styles[col]
                if adaptive_col_width:
                    col_widths[col] = max(col_widths[col], ExcelUtils.calc_cell_width(cell))
                style.num_format_str = ExcelUtils.get_cell_style(cell)
                sheet.write(offset + row, col, cell, style)
                if adaptive_row_height:
                    max_row = max(max_row, len(str(cell).split("\n")))
            if adaptive_row_height:
                ExcelUtils.set_row_height(sheet, offset + row, max_row)
        return col_widths

    @staticmethod
    def add_tips(sheet: Worksheet, cols: int, tips: str) -> None:
        if not tips:
            return

        tips_style = XFStyle()
        ft = Font()
        ft.bold = True
        ft.colour_index = 52
        al = Alignment()
        al.horz = Alignment.HORZ_LEFT  # 设置左对齐
        al.vert = Alignment.VERT_CENTER  # 设置垂直居中
        al.wrap = Alignment.WRAP_AT_RIGHT  # 设置自动换行
        tips_style.alignment = al
        tips_style.font = ft
        sheet.write_merge(0, 0, 0, cols, tips, tips_style)

    @staticmethod
    def write_merge_data(  # pylint: disable=too-many-locals
        sheet: Worksheet,
        excel_data: list[list[list[CellData]]],
        offset: int = 0,
        *,
        col_styles: Optional[list[Optional[XFStyle]]] = None,
        adaptive_col_width: bool = False,
        adaptive_row_height: bool = False,
    ) -> list[int]:
        style = ExcelUtils.gen_style()
        mg_style = ExcelUtils.gen_merge_style()
        col_widths = [0] * len(excel_data[0][0]) if excel_data and excel_data[0] else []
        for vals in excel_data:
            for row, row_data in enumerate(vals):
                max_row = 1
                for col, cell in enumerate(row_data):
                    if cell.is_none:
                        continue
                    ft = Font()
                    if cell.set_colour:
                        ft.colour_index = cell.colour_index
                    if cell.is_combo:
                        if col_styles and col < len(col_styles) and col_styles[col]:
                            mg_style = col_styles[col]
                        mg_style.num_format_str = ExcelUtils.get_cell_style(cell.data)
                        mg_style.font = ft
                        sheet.write_merge(offset + row, offset + row + len(vals) - 1, col, col, cell.data, mg_style)
                    else:
                        if col_styles and col < len(col_styles) and col_styles[col]:
                            style = col_styles[col]
                        style.num_format_str = ExcelUtils.get_cell_style(cell.data)
                        style.font = ft
                        sheet.write(offset + row, col, cell.data, style)
                    if adaptive_col_width:
                        col_widths[col] = max(col_widths[col], ExcelUtils.calc_cell_width(cell.data))
                    if adaptive_row_height:
                        max_row = max(max_row, len(str(cell.data).split("\n")))
                if adaptive_row_height:
                    ExcelUtils.set_row_height(sheet, offset + row, max_row)
            offset += len(vals)
        return col_widths

    @staticmethod
    def set_column_widths(
        sheet: Worksheet,
        header_col_widths: list[int],
        content_col_widths: list[int],
        *,
        adaptive_col_width: bool = False,
        col_widths: Optional[dict[int, int]] = None,
    ) -> None:
        cols = len(header_col_widths)
        default_widths = [0x0D00 + 2000] * cols
        if not adaptive_col_width:
            header_col_widths = content_col_widths = default_widths
        if not header_col_widths:
            header_col_widths = default_widths
        if not content_col_widths:
            content_col_widths = default_widths

        if col_widths:
            for i, width in col_widths.items():
                header_col_widths[i] = width
                content_col_widths[i] = width

        for i, (header_width, content_width) in enumerate(zip(header_col_widths, content_col_widths)):
            column: Column = sheet.col(i)
            column.width = max(header_width, content_width)

    @staticmethod
    def add_merge_sheet(  # pylint: disable=too-many-arguments
        work_book: Workbook,
        title: str,
        headers: list[list[str]],
        excel_data: list[list[list[CellData]]],
        *,
        tips: str = "",
        header_styles: Optional[list[Optional[XFStyle]]] = None,
        col_widths: Optional[dict[int, int]] = None,
        adaptive_col_width: bool = False,
        adaptive_row_height: bool = False,
    ) -> None:
        sheet: Worksheet = work_book.add_sheet(title)
        ExcelUtils.add_tips(sheet, len(headers[0]), tips)
        offset = 1 if tips else 0
        header_col_widths = ExcelUtils.write_data(
            sheet,
            headers,
            offset=offset,
            col_styles=header_styles,
            adaptive_col_width=adaptive_col_width,
            adaptive_row_height=adaptive_row_height,
        )
        offset += 1
        content_col_widths = ExcelUtils.write_merge_data(
            sheet,
            excel_data,
            offset=offset,
            adaptive_col_width=adaptive_col_width,
            adaptive_row_height=adaptive_row_height,
        )

        ExcelUtils.set_column_widths(
            sheet, header_col_widths, content_col_widths, adaptive_col_width=adaptive_col_width, col_widths=col_widths
        )

    @staticmethod
    def get_excel_ostream(work_book: Workbook) -> BytesIO:
        ostream = BytesIO()
        work_book.save(ostream)
        ostream.seek(0)
        return ostream

    @staticmethod
    def gen_merge_data(  # pylint: disable=too-many-arguments
        headers: list[list[str]],
        title: str,
        data: list[list[list[CellData]]],
        *,
        tips: str = "",
        header_styles: Optional[list[Optional[XFStyle]]] = None,
        col_widths: Optional[dict[int, int]] = None,
        adaptive_col_width: bool = False,
        adaptive_row_height: bool = False,
    ) -> BytesIO:
        work_book = ExcelUtils.new_workbook()
        ExcelUtils.add_merge_sheet(
            work_book,
            title,
            headers,
            data,
            tips=tips,
            header_styles=header_styles,
            col_widths=col_widths,
            adaptive_col_width=adaptive_col_width,
            adaptive_row_height=adaptive_row_height,
        )
        return ExcelUtils.get_excel_ostream(work_book)

    @staticmethod
    def convert_data(data: list[list[str]], *, cols: int = 0) -> list[list[list[CellData]]]:
        max_rows = max(len(rows) for rows in data)
        res = []

        merge_row: list[list[CellData]] = []
        for rows in data:
            if len(rows) < max_rows:
                rows += ["" for _ in range(max_rows - len(rows))]
            if cols > 0:
                if merge_row:
                    if "_".join(x for x in rows[:cols]) == "_".join(x.data for x in merge_row[-1][:cols]):
                        merge_row.append(
                            [CellData(data=x, is_combo=i < cols, is_none=i < cols) for i, x in enumerate(rows)]
                        )
                    else:
                        res.append(merge_row)
                        merge_row = [[CellData(data=x, is_combo=i < cols, is_none=False) for i, x in enumerate(rows)]]
                else:
                    merge_row.append([CellData(data=x, is_combo=i < cols, is_none=False) for i, x in enumerate(rows)])
            else:
                res.append([[CellData(data=x) for x in rows]])
        if merge_row:
            res.append(merge_row)
        return res

    @staticmethod
    def save_to_file(filename: str, content: BytesIO) -> None:
        with open(filename, "wb+") as f:
            f.write(content.getvalue())


def test1() -> None:
    example_data = [
        {
            "title": "测试用例",
            "topic": {
                "title": "支付宝",
                "topics": [
                    {
                        "title": "首页",
                        "topics": [
                            {"title": "搜索能力"},
                            {
                                "title": "热区广告",
                                "topics": [
                                    {"title": "浏览广告"},
                                    {"title": "关注广告"},
                                    {"title": "推荐广告"},
                                ],
                            },
                        ],
                    },
                    {
                        "title": "设置页",
                        "topics": [
                            {"title": "修复用户信息"},
                            {
                                "title": "修改通用设置",
                                "topics": [
                                    {"title": "修改布局"},
                                    {"title": "修改语言"},
                                    {"title": "修改主题"},
                                ],
                            },
                        ],
                    },
                ],
            },
            "structure": "org.xmind.ui.logic.right",
        }
    ]
    # xmid_info = XmindUtils.get_xmind("/tmp/test1.xmind")
    xmid_info = XmindInfo(root=example_data)
    inst = XmindUtils(xmid_info)
    data = inst.build()
    headers = [
        [
            "所属产品",
            "所属模块",
            "相关需求",
            "用例标题",
        ]
    ]
    context = ExcelUtils.gen_merge_data(
        headers,
        xmid_info.root[0].title,
        ExcelUtils.convert_data(data, cols=3),
        adaptive_col_width=True,
        adaptive_row_height=True,
    )
    ExcelUtils.save_to_file("/tmp/test1.xls", context)


if __name__ == "__main__":
    test1()
