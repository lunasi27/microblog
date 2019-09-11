from app import es
import pdb

# Elasticsearch与Flask整合教程 https://www.jianshu.com/p/56cfc972d372

# 这样做的好处就是把所有和ES有关的代码都放在search文件里，以后如果要修改查询引擎，只需要修改这一个文件就好了
def add_to_index(index, model):
    # 在指定id的情况下向ES的数据库插入数据，若不存在就插入，若存在则更新
    if not es:
        return
    payload = {}
    for field in model.__searchable__:
        payload[field] = getattr(model, field)
    es.index(index=index, id=model.id, body=payload)


def remove_from_index(index, model):
    if not es:
        return
    es.delete(index=index, id=model.id)


def query_index(index, query, page, per_page):
    if not es:
        return [], 0
    body = {
        # match和multi_match的不同在于，multi_match可以跨多个字段搜索
        # 通过*传递字段名称，表示所有字段
        # 这个里使用*是为了通用化，因为不同的索引中字段名称可能不同
        'query': {'multi_match': {'query': query, 'fields': ['*']}},
        # from和size参数控制整个结果集中，哪些数据需要被返回
        'from': (page - 1) * per_page, 'size': per_page
    }
    search = es.search(index=index, body=body)
    ids = [int(hit['_id']) for hit in search['hits']['hits']]
    total = int(search['hits']['total']['value'])
    return ids, total
