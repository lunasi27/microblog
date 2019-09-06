#!/flask/venv/bin/python


import imp
from migrate.versioning import api
from app import db
from config import SQLALCHEMY_DATABASE_URI
from config import SQLALCHEMY_MIGRATE_REPO

# 基本原理，比较数据库中的模型结构与本地类定义的模型结构之间的区别。然后生成一个迁移脚本，存放在迁移仓库中。
# 最好不要重命名字段，否则会出现字段找不到的情况。
# 不要在生产环境运行这个脚本，这个只是在开发阶段用的。
# 最好检察每一份自动生成的迁移脚本。


# 获取当前数据库变化的版本号
v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
# 生成迁移脚本的文件名
migration = SQLALCHEMY_MIGRATE_REPO + ('/versions/%03d_migration.py' % (v+1))
tmp_module = imp.new_module('old_model')
old_model = api.create_model(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
exec(old_model, tmp_module.__dict__)
# 查找数据库变化差值，生成转换脚本
script = api.make_update_script_for_model(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO, tmp_module.meta, db.metadata)
open(migration, 'wt').write(script)
# 执行数据库迁移
api.upgrade(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
# 获取迁移后的版本号
v = api.db_version(SQLALCHEMY_DATABASE_URI, SQLALCHEMY_MIGRATE_REPO)
print('New migration saved at %s' % migration)
print('Current database version: %s' % v)
