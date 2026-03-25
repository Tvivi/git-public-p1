import pytest_bdd

# NOTE: featureフォルダと、conftestファイル、本テストファイルの相対パスの位置が
# 上手く合わせておかないとFileNotFoundになる。具体的には同じ階層のディレクトリ
pytest_bdd.scenarios("features/calculator.feature")
