#!/bin/bash
user_name=seekplum
user_group=staff

packages_name=mysql-5.7.22-macos10.13-x86_64
packages_dir=/Users/$user_name/packages
source_mysql_dir=$packages_dir/$packages_name
link_mysql_dir=$packages_dir/mysql
mysql_data=$packages_dir/mysql/data
new_mysql_server=$packages_dir/mysql.server

admin_user=pig

admin_pass='pig'

logs=/tmp/summary.log

# ulimit -SHn 300000
rm -f $logs
touch $logs

# 检查安装包是否存在
# if [ ! -f "${source_mysql_dir}.tar.gz" -a ! -f "${source_mysql_dir}.tar" ];then
#    echo "未发现二进制安装包${source_mysql_dir}.tar.gz 或 ${source_mysql_dir}.tar,脚本退出！！" |tee -a $logs
#    exit 1
# fi

# 检查安装目录是否存在
if [ ! -d "$source_mysql_dir" ];then
    echo "未发现安装包${source_mysql_dir}，脚本退出！！" |tee -a $logs
    exit 1
fi

# 检查mysql.server是否存在
if [ ! -f "$new_mysql_server" ];then
    echo "未发现二进制${new_mysql_server}，脚本退出！！" |tee -a $logs
    exit 1
fi

# 安装MySQL
install_mysql() {
    # kill mysql进程
    pkill -9 mysql
    pkill -9 mysqld
    pkill -9 mysqld_safe

    # 对之前的mysql进行解链
    if [ -L $link_mysql_dir ];then
        unlink $link_mysql_dir
    fi

    # echo 如果mysql目录不是一个链接,而是一个目录,则先进行备份,然后再删除
    # [ -d $link_mysql_dir ] && cp -ar $link_mysql_dir $link_mysql_dir.bak_`date +%F_%H_%M_%S`

    # 删除旧的mysql
    rm -rf $link_mysql_dir
    ln -s $source_mysql_dir $link_mysql_dir

    # 创建相关目录
    rm -rf $mysql_data/*
    mkdir -p $mysql_data/{innodb_log,innodb_ts,log,mydata,relaylog,slowlog,sock,tmpdir,undo,conf}
    touch $mysql_data/log/error.log
    echo -e "create mysql error.log"

    # mysql.server 会和conf配置有关，需要手动修改
    cp $new_mysql_server $source_mysql_dir/support-files/

    # 设置开机自启动
    # rm -f /etc/init.d/mysql
    # cp $link_mysql_dir/support-files/mysql.server /etc/init.d/mysql
    # chmod +x /etc/init.d/mysql
    # chkconfig --add mysql
    # chkconfig --level 2345 mysql on
    # echo -e "set mysql autostart"

    # 设置mysql动态连接 |tee -a $logs
    # echo $link_mysql_dir/lib > /etc/ld.so.conf.d/mysql.conf
    # ldconfig

    # 生成配置文件 |tee -a $logs
    # 查询内存大小
    # let "_buffer_pool_size=$(free -g |grep Mem |awk '{print $2}') * 1000 / 100 * 40"
    let "_buffer_pool_size=16 * 1000 / 100 * 40"
    let "_buffer_pool_size=($_buffer_pool_size / 128 + 1)*128"
    # echo -e "set mysql _buffer_pool_size" |tee -a $logs

    # 截取ip的最后一位
    last=`ifconfig en0 | awk '/inet /{print $2}' | awk -F. '{print $NF}'`  # 注意端口号
    let "serverid=${last}+3306"

    cat > $mysql_data/conf/my.cnf  << EOF
[client]
loose_default-character-set = utf8
port = 3306
socket = $mysql_data/sock/mysql.sock
user = admin

[mysqldump]
quick
max_allowed_packet = 2G
default-character-set = utf8

[mysql]
no-auto-rehash
show-warnings
prompt = "\\u@\\h : \\d \\r:\\m:\\s> "
default-character-set = utf8

[myisamchk]
key_buffer = 512M
sort_buffer_size = 512M
read_buffer = 8M
write_buffer = 8M

[mysqlhotcopy]
interactive-timeout

[mysqld_safe]
user = mysql
open-files-limit = 65535

[mysqld]
default-storage-engine = INNODB
character-set-server = utf8
collation_server = utf8_bin
log_timestamps = SYSTEM
user = ${user_name}
port = 3306
socket = $mysql_data/sock/mysql.sock
pid-file = $mysql_data/mydata/mysql.pid
datadir = $mysql_data/mydata
basedir = $packages_dir/mysql
tmpdir = $mysql_data/tmpdir
skip-name-resolve
skip_external_locking
lower_case_table_names = 1
event_scheduler = 0
back_log = 512
default-time-zone = '+8:00'
max_connections = 1000
max_connect_errors = 99999
max_allowed_packet = 64M
slave_pending_jobs_size_max = 128M
max_heap_table_size = 8M
max_length_for_sort_data = 16k
wait_timeout = 172800
interactive_timeout = 172800
net_buffer_length = 8K
read_buffer_size = 2M
read_rnd_buffer_size = 2M
sort_buffer_size = 2M
join_buffer_size = 4M
binlog_cache_size = 2M
table_open_cache = 4096
table_open_cache_instances = 2
table_definition_cache = 4096
thread_cache_size = 512
tmp_table_size = 8M
query_cache_size = 0
query_cache_type = OFF
max_prepared_stmt_count = 163820
secure_file_priv = null
innodb_open_files = 65535
log-error = $mysql_data/log/error.log
log-bin = mysql-bin
long_query_time = 1
slow_query_log
slow_query_log_file = $mysql_data/slowlog/slow-query.log
log_warnings
log_slow_slave_statements
server_id = ${serverid}
binlog-checksum = CRC32
binlog-rows-query-log-events = 1
binlog_max_flush_queue_time = 1000
max_binlog_size = 512M
sync_binlog = 1
master-verify-checksum = 1
master-info-repository = TABLE
auto_increment_increment = 2
relay-log = $mysql_data/relaylog/relay_bin
relay-log-info-repository = TABLE
relay-log-recovery = 1
slave-sql-verify-checksum = 1
log_slave_updates = 1
slave-net-timeout = 10
key_buffer_size = 8M
bulk_insert_buffer_size = 8M
myisam_sort_buffer_size = 64M
myisam_max_sort_file_size = 10G
myisam_repair_threads = 1
myisam_recover_options = force
innodb_data_home_dir = $mysql_data/innodb_ts
innodb_data_file_path = ibdata1:2G:autoextend
innodb_file_per_table
innodb_file_format = barracuda
innodb_file_format_max = barracuda
innodb_file_format_check = ON
innodb_strict_mode = 1
innodb_flush_method = O_DIRECT
innodb_checksum_algorithm = crc32
innodb_autoinc_lock_mode = 2
innodb_buffer_pool_size = ${_buffer_pool_size}M
innodb_buffer_pool_instances = 8
innodb_max_dirty_pages_pct = 50
innodb_adaptive_flushing = ON
innodb_flush_neighbors = 0
innodb_lru_scan_depth = 4096
innodb_change_buffering = all
innodb_old_blocks_time = 1000
innodb_buffer_pool_dump_pct = 50
innodb_buffer_pool_dump_at_shutdown = ON
innodb_buffer_pool_load_at_startup = ON
innodb_adaptive_hash_index_parts = 32
innodb_log_group_home_dir = $mysql_data/innodb_log
innodb_log_buffer_size = 128M
innodb_log_file_size = 2G
innodb_log_files_in_group = 2
innodb_flush_log_at_trx_commit = 1
innodb_fast_shutdown = 1
innodb_support_xa = ON
innodb_thread_concurrency = 64
innodb_lock_wait_timeout = 120
innodb_rollback_on_timeout = 1
performance_schema = on
innodb_read_io_threads = 8
innodb_write_io_threads = 16
innodb_io_capacity = 20000
innodb_use_native_aio = 1
innodb_undo_directory = $mysql_data/undo
innodb_purge_threads = 4
innodb_purge_batch_size = 512
innodb_max_purge_lag = 65536
innodb_undo_tablespaces = 8 # cannot modify
innodb_undo_log_truncate = ON # 5.7 only
innodb_max_undo_log_size = 2G  # 5.7 only
gtid-mode = on # GTID only
enforce-gtid-consistency = true # GTID only
optimizer_switch = 'mrr=on,mrr_cost_based=off,batched_key_access=on'
# explicit_defaults_for_timestamp = ON
slave_preserve_commit_order = ON
slave_parallel_workers = 8
slave_parallel_type = LOGICAL_CLOCK
transaction_isolation = READ-COMMITTED
binlog-format = ROW
log_bin_trust_function_creators = 1
expire_logs_days = 15
innodb_page_cleaners = 4
auto_increment_offset=1
EOF


    # echo 对配置文件做软链 |tee -a $logs
    # unlink /etc/my.cnf &> /dev/null
    # [ $? -ne 0 ] && rm -f /etc/my.cnf
    # ln -s $mysql_data/conf/my.cnf  /etc/my.cnf

    # 修改文件夹权限为我们创建的MySQL用户 |tee -a $logs
    # chown -R ${user_name}:$user_group $link_mysql_dir
    chmod -R 755 $link_mysql_dir

    # 创建用户
    # $link_mysql_dir/bin/mysql_install_db --defaults-file=$mysql_data/conf/my.cnf --basedir=$link_mysql_dir --datadir=$mysql_data/mydata --user=mysql

    echo ======  init mysql...
    # $link_mysql_dir/bin/mysqld  --defaults-file=$mysql_data/conf/my.cnf --initialize-insecure --basedir=$link_mysql_dir --datadir=$mysql_data/mydata --user=mysql
    $link_mysql_dir/bin/mysqld --defaults-file=$mysql_data/conf/my.cnf  --initialize --user=mysql
    $link_mysql_dir/bin/mysql_ssl_rsa_setup --defaults-file=$mysql_data/conf/my.cnf
    # $link_mysql_dir/bin/mysqld_safe --defaults-file=$mysql_data/conf/my.cnf --user=mysql

    # 拷贝二进制文件
    # cp $packages_dir/mysql/bin/mysql /usr/local/bin/
}

install_mysql
echo | tee -a $logs

if [ "$SECONDS" -ge 60 ];then
    let "runtimes=${SECONDS}/60"
    echo -e "install_time consuming:${runtimes}min" |tee -a $logs
    echo "==============================================================`date`" |tee -a $logs

else
    runtimes=${SECONDS}
    echo -e "install_time consuming:${runtimes}s" |tee -a $logs
    echo "==============================================================`date`" |tee -a $logs
fi


# 连接mysql
# /Users/seekplum/packages/mysql/bin/mysql -upig -pig -S /Users/seekplum/packages/data/sock/
