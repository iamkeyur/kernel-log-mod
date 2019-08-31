from models import db, Log


def create_tables():
    db.connect()
    db.create_tables([Log], safe=True)


# def get_all_repos() -> [Repo]:
#     return Repo.select()
#
#
# def get_logs_of_repo(repo: Repo) -> [Log]:
#     return Log.select().join(Commit)\
#         .where((Commit.repo == repo.url) & (Commit.is_merge_commit == False))\
#         .order_by(Commit.committed_date.desc())
#
#
# def get_repo_with_url(url):
#     return Repo.get_or_none(Repo.url == url)
