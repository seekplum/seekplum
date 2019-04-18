#!/usr/bin/env python
# -*- coding:utf-8 -*-
import re


def get_gen(lines, pattern):
    """
    按pattern正则分割lines,分割结果有pattern和下个pattern之间的值组成的生成器
    :param lines: cmd 执行结果
    :param pattern: 正则表达式
    :return:
    """

    def _get_split_line_number(lines_list, pattern):
        """
        split the lines by regex pattern
        pattern is the compiled regex expression
        """
        line_num = []
        for i, line in enumerate(lines_list):
            if pattern.search(line):
                line_num.append(i)
        line_num.append(len(lines_list))
        return line_num

    if not lines:
        raise StopIteration

    line_list = lines.splitlines()
    line_num = _get_split_line_number(line_list, pattern)

    if len(line_num) <= 1:
        raise StopIteration

    for i in range(1, len(line_num)):
        yield "\n".join(line_list[line_num[i - 1]:line_num[i]])


def parser_pdisk(output):
    """
    把执行结果转为字典
    :param output: cmd 执行结果
    :return:
    """
    physical_array = {}
    pattern_array = re.compile("^\s+(array\s+\w+|unassigned)\s*$")
    gens = get_gen(output, pattern_array)
    for array_section in gens:
        result = get_physical_array(array_section)
        physical_array.update(result)
    return physical_array


def get_info_child(lines, pattern, pattern_ID=None, keepid=False):
    """
    分析最小段落属性，返回一个字典，pattern_ID用来匹配得到段落的ID, 通过pattern来组合字典
    :param lines:
    :param pattern:
    :param pattern_ID:
    :param keepid:
    :return:
    """
    if not pattern_ID:
        pattern_ID = pattern
    line_list = lines.splitlines()
    find_ID = False
    for line_ID in line_list:
        match = pattern_ID.search(line_ID)
        if match:
            ID = match.groups()
            if not keepid:
                line_list.remove(line_ID)
            find_ID = True
            break
    if not find_ID:
        return
    info = parse_lines("\n".join(line_list))
    return (ID, info)


def parse_lines(lines, begin=None, end=None):
    """
    将lines中数据按：分割， 把字符串转为字典
    :param lines:
    :param begin:
    :param end:
    :return:
    """
    info_dict = {}
    line_list = lines.splitlines()
    if not begin:
        begin = 0
    if not end:
        end = len(line_list) + 1
    for line in line_list[begin: end]:
        line = line.strip()
        if not line:
            continue
        key = line.split(":", 1)[0].strip()
        key = "_".join(key.split())
        try:
            value = line.split(":", 1)[1].strip()
        except:
            value = ""
        info_dict[key] = value
    return info_dict


def get_physical_array(physical_section):
    """
    处理physical_section，使之成为字典
    :param physical_section:
    :return:
    """
    pattern_father = re.compile("^\s+(array\s+\w+|unassigned)\s*$")
    pattern_child = re.compile("^\s+physicaldrive\s+(.*)$")
    father_result = GetInfo_Father(physical_section, pattern_father, pattern_child)
    array_id = father_result[0][0]
    gens = get_gen(physical_section, pattern_child)
    physical_info = {}
    for gen in gens:
        result = get_info_child(gen, pattern_child)
        key = result[0][0].strip()
        value = result[1]
        physical_info[key] = value
    array = {}
    array[array_id] = physical_info
    return array


def GetLines(lines, pattern_begin, pattern_end=None):
    """
    返回pattern_begin到pattern_end(不包括pattern_end)之间的内容
    :param lines:
    :param pattern_begin:
    :param pattern_end:
    :return:
    """
    line_list = lines.splitlines()
    # 找到pattern_begin的行号
    find_begin = False
    for line_begin, line in enumerate(line_list):
        match = pattern_begin.findall(line)
        if match:
            find_begin = True
            break
    if not find_begin:
        return

    # the pattern_begin matches the last line
    if len(line_list) == line_begin + 1:
        return line_list[line_begin]

    if not pattern_end:
        line_list = line_list[line_begin:]
        return "\n".join(line_list)

    # 找到pattern_end的行号
    find_end = False
    for line_end, line in enumerate(line_list[line_begin + 1:]):
        match = pattern_end.findall(line)
        if match:
            find_end = True
            break
    if not find_end:
        line_list = line_list[line_begin:]
        return "\n".join(line_list)
    # 不包括line_end， 之前 find_end 中加了 1
    line_end = line_begin + line_end + 1

    # get the result
    if line_begin == line_end:
        return lines
    line_list = line_list[line_begin: line_end]
    return "\n".join(line_list)


def GetInfo_Father(lines, pattern_father, pattern_child, pattern_ID=None):
    """
    分析pattern_father与pattern_child之间的段落属性，
    返回pattern_father属性字典,pattern_ID用来得到段落的ID
    :param lines:
    :param pattern_father:
    :param pattern_child:
    :param pattern_ID:
    :return:
    """
    if not pattern_ID:
        pattern_ID = pattern_father
    info = {}
    father = GetLines(lines, pattern_father, pattern_child)
    if not father:
        return (None, info)

    father_list = father.splitlines()
    # 取得ID
    find_ID = False
    for line_ID in father_list:
        match = pattern_ID.search(line_ID)
        if match:
            # 获取 pattern_ID 中的值
            ID = match.groups()
            father_list.remove(line_ID)
            find_ID = True
            break
    if not find_ID:
        return
    lines_section = "\n".join(father_list)
    info = parse_lines(lines_section)
    return (ID, info)


if __name__ == "__main__":
    with open('cmd_parser.txt', 'r') as f:
        output = f.read()
    result = parser_pdisk(output)
    print "result:", result
