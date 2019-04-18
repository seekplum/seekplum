#/bin/bash

RETVAL=0

install_zsh() {
    echo -e '\033[32mInstall zsh\033[0m'
	yum install zsh -y

	# 安装 oh-my-zsh主题
	sh -c "$(wget https://raw.github.com/robbyrussell/oh-my-zsh/master/tools/install.sh -O -)" <<EOF
exit
EOF

    # 设置命令行补齐
	git clone git://github.com/zsh-users/zsh-autosuggestions ~/.oh-my-zsh/custom/plugins/zsh-autosuggestions
	zsh_bash=~/.zshrc
    start_line=`cat -n $zsh_bash |grep -E 'plugins=\($'|awk '{print $1}'|sed -n '1'p`
    end_line=$(($start_line+2))
    del_command='sed -i '${start_line},${end_line}d' '${zsh_bash}''
    echo -e '\033[32m'${del_command}'\033[0m'
    $del_command

    cat >> $zsh_bash <<EOF
plugins=(
    zsh-autosuggestions
    git
)
EOF
    chsh -s /bin/zsh
    echo "source ~/.bash_profile" >> ${zsh_bash}
    echo "source ~/.bashrc" >> ${zsh_bash}
}

remove_zsh() {
    echo -e '\033[31mRemove zsh\033[0m'
    chsh -s /bin/bash
    yum remove -y zsh >/dev/null 2>&1
    rm -f ~/.zsh*
    rm -rf ~/.oh-my-zsh
}

remove_docker() {
    echo -e '\033[31mRemove Docker\033[0m'
    systemctl stop docker >/dev/null 2>&1
    yum remove -y docker-engine >/dev/null 2>&1
    find / -name "*docker*" | grep -v "oh-my-zsh" | xargs rm -rf
}

install_docker() {
    echo -e '\033[32mInstall Docker\033[0m'
    # 添加repo源
    cat > /etc/yum.repos.d/docker.repo <<EOF
[dockerrepo]
name=Docker Repository
baseurl=https://yum.dockerproject.org/repo/main/centos/7/
enabled=1
gpgcheck=1
gpgkey=https://yum.dockerproject.org/gpg
EOF
    yum -y install docker-engine
    systemctl start docker
}

install() {
	install_zsh
	install_docker
}

# 打印帮助信息
print_help() {
	echo "Usage: bash $0 {install|install_docker|install_zsh|remove_docker|remove_zsh}"
    echo "e.g: $0 install"
}

# 命令行参数大于 1 时打印提示信息后退出
if [ $# -gt 1 ] ; then
    print_help
    exit 1;
fi


case "$1" in
  install_docker)
	install_docker
	;;
  install_zsh)
	install_zsh
	;;
  remove_zsh)
	remove_zsh
	;;
  remove_docker)
	remove_docker
	;;
  "")
  # -h|--help)
	install  # 参数为空时执行
	;;
  *)  # 匹配都失败执行
	print_help
	exit 1
esac

exit $RETVAL
