import json

import pymysql
from algosdk import mnemonic
from algosdk.future import transaction
from algosdk.v2client import algod


class Record:
    def __init__(self, address: str, asset_id: int, completed: str):
        self.address = address
        self.asset_id = asset_id
        self.completed = completed

    def __repr__(self):
        return f"{self.address} - {self.asset_id} completed: {self.completed}"


def payer_account() -> dict:
    # 替换为自己的助记词
    m = ""
    return {
        'public_key': mnemonic.to_public_key(m),
        'private_key': mnemonic.to_private_key(m)
    }


def algod_client(testnet):
    if (testnet == True):
        print("启用测试网")
        algod_address = "https://api.testnet.algoexplorer.io"
    elif (testnet == False):
        print("启用生产网")
        algod_address = "https://api.algoexplorer.io"

    algod_token = ""
    headers = {'User-Agent': 'py-algorand-sdk'}
    algod_client = algod.AlgodClient(algod_token, algod_address, headers)
    status = algod_client.status()
    print(f"algo status {status}")
    return algod_client


def not_completed_list() -> list[Record]:
    record_list = []
    db = pymysql.connect(host='localhost',
                         user='root',
                         port=3306,
                         password='123456',
                         database='tiger')
    select_sql = f"""
    select `address`,`asset_id`,`completed` from `tb_transfer_record` where `completed` = 'NO' 
    """
    print(f"预计查询脚本:{select_sql}")

    # 使用cursor()方法获取操作游标
    cursor = db.cursor()

    # SQL 查询语句
    try:
        # 执行sql语句
        cursor.execute(select_sql)
        # 获取所有记录列表
        results = cursor.fetchall()
        for row in results:
            address = row[0]
            asset_id = row[1]
            completed = row[2]
            # 打印结果
            record_list.append(Record(address, asset_id, completed))
    except Exception as e:
        # 如果发生错误则回滚
        db.rollback()
        print(f"数据库发生错误回滚: {e}")
    # 关闭数据库连接
    db.close()
    return record_list


def has_asset(algodclient, address, asset_id) -> bool:
    # account_info = algodclient.account_info(address)
    # print(f"account info: {json.dumps(account_info, indent=4)}")
    # 检查资产是否有余额
    account_info = algodclient.account_info(address)
    for idx in range(0, len(account_info['assets'])):
        scrutinized_asset = account_info['assets'][idx]
        if scrutinized_asset['asset-id'] == asset_id and scrutinized_asset['amount'] > 0:
            print("{} has opt-in asset {},and has transferred ".format(address, scrutinized_asset['asset-id']))
            return True
    return False


def wait_for_confirmation(client, txid):
    """
    Utility function to wait until the transaction is
    confirmed before proceeding.
    """
    last_round = client.status().get('last-round')
    txinfo = client.pending_transaction_info(txid)
    while not (txinfo.get('confirmed-round') and txinfo.get('confirmed-round') > 0):
        print("Waiting for confirmation")
        last_round += 1
        client.status_after_block(last_round)
        txinfo = client.pending_transaction_info(txid)
    print("Transaction {} confirmed in round {}.".format(txid, txinfo.get('confirmed-round')))
    return txinfo


def transfer_asset(algod_client, address, asset_id) -> bool:

    try:
        params = algod_client.suggested_params()
        # comment these two lines if you want to use suggested params
        params.fee = 1000
        params.flat_fee = True

        # 构建交易参数
        sender = payer_account()
        # create the asset transfer transaction
        txn = transaction.AssetTransferTxn(sender['public_key'], params, address, 1, asset_id)

        # sign the transaction
        signed_txn = txn.sign(sender['private_key'])
        print("签署交易成功")

        txid = algod_client.send_transaction(signed_txn)
        print(f"{txid} 交易发送成功，待确认")

        wait_for_confirmation(algod_client, txid)
        ptx = algod_client.pending_transaction_info(txid)
        print("交易成功")
        return True
    except Exception as e:
        print(f"交易异常，不更新状态: {e}")
        return False


def update_completed(address, asset_id):
    db = pymysql.connect(host='localhost',
                         user='root',
                         password='123456',
                         database='tiger')
    update_sql = f"""
    update `tb_transfer_record` set `completed` = 'YES' where `address` = '{address}' and asset_id = '{asset_id}' 
    """
    print(f"预计查询脚本:{update_sql}")

    # 使用cursor()方法获取操作游标
    cursor = db.cursor()

    # SQL 查询语句
    try:
        # 执行sql语句
        cursor.execute(update_sql)
        db.commit()
    except Exception as e:
        # 如果发生错误则回滚
        db.rollback()
        print(f"数据库发生错误回滚: {e}")
    # 关闭数据库连接
    db.close()


if __name__ == '__main__':
    """
    1. 获取本地未完成的asset_id
    2. 调用接口查询钱包是否存在asset，
        2.1 存在：log
        2.2 不存在：
            检查对应收获地址是否存在，
                存在：更新状态
                不怒在：告警，是否需要手动更新
    3. 查询所有未完成的资产
    4. 发送交易
        1. 成功：更新状态
        2. 失败：等待下次同步状态
    """
    # 获取本地未完成的asset_id
    algod_client = algod_client(testnet=True)
    need_sync_status_list = not_completed_list()
    print(f"待同步状态列表:{need_sync_status_list}")
    count = 1
    for each in need_sync_status_list:
        print(f"正在更新第{count}个地址的资产状态:{each.address}")
        if has_asset(algod_client, each.address, each.asset_id):
            print(f"{each.address} has translated by {each.asset_id}")
            # 更新资产状态
            update_completed(each.address, each.asset_id)
        count += 1

    need_transfer_list = not_completed_list()
    print(f"准备转移列表:{need_transfer_list}")
    for each in need_transfer_list:
        if transfer_asset(algod_client, each.address, each.asset_id):
            # 转账成功，更新状态
            update_completed(each.address, each.asset_id)
