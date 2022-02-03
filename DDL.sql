create database `tiger` default character set utf8 collate utf8_general_ci;

use tiger;

-- 用户信息表
create table `tb_transfer_record` (
    `id` bigint(20) primary key auto_increment,
    `address` varchar(255) NOT null comment '钱包地址',
    `asset_id` bigint not null comment '资产id',
    `completed` varchar(8) default null comment '完成状态 NO未完成，YES已完成',
    `create_time` datetime not null default current_timestamp  comment '创建时间',
    `update_time` datetime not null default current_timestamp on update current_timestamp comment '创建时间',
    unique key `uk_address_asset` (`address`,`asset_id`) USING BTREE
) engine=InnoDB default charset='utf8' comment='资产转移记录表';
