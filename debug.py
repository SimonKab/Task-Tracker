from tasktracker_server.storage.sqlite_peewee_adapters import ProjectStorageAdapter

adapter = ProjectStorageAdapter()
relations = adapter._get_all_relations()
for relation in relations:
    print(relation.__data__)