# batch-transfer-service
批量发送algorand - NFT 到指定账户

## 预备
1. python3
2. docker
3. docker-compose

## 配置
### 连接数据库
- username: root
- password: 123456
进入tiger数据库  
配置对应接收钱包与接收资产的对应关系
```sql
INSERT INTO `tiger`.`tb_transfer_record` (`address`, `asset_id`, `completed`) VALUES ('xxx', xxx, 'NO'); 
```
### 配置启动网络
在main.py文件中，找到 178 行
```python
algod_client = algod_client(testnet=True)
```
将testnet改为相应环境的配置
- True : 测试网
- False : 正式网

### 配置发送账户
打开main.py 文件,找到 payer_account 填充助记词到m变量中
```py
def payer_account() -> dict:
    # 替换为自己的助记词
    m = ""
    return {
        'public_key': mnemonic.to_public_key(m),
        'private_key': mnemonic.to_private_key(m)
    }
```
## 启动
### 启动数据库
```shell
sh ./startup.sh
```
### 运行脚本
```shell
python ./main.py
```


## 关闭
```shell
sh ./shutdown.sh
```
## 优化项
1. 系统配置项迁移至数据库，或者环境变量
2. 接收账户余额不足时，发送最低接收资产余额
3. 数据库连接池
4. 模板化重构代码