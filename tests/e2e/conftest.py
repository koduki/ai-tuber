import pytest
import os

@pytest.fixture(scope="session")
def docker_compose_file(pytestconfig):
    """
    docker-compose.ymlの場所を指定する。
    プロジェクトルートのファイルを使用。
    """
    return os.path.join(str(pytestconfig.rootdir), "docker-compose.yml")

@pytest.fixture(scope="session")
def docker_compose_project_name():
    """プロジェクト名の重複を避けるために一意な名前を。"""
    return "ai-tuber-e2e"

@pytest.fixture(scope="session")
def docker_ip():
    """
    デブコンテナ内からホスト側のIPを解決するためのフィクスチャ。
    """
    import socket
    import os
    
    # GitHub Actions (CI) 環境では localhost (127.0.0.1) を使用
    if os.getenv("GITHUB_ACTIONS") == "true":
        return "127.0.0.1"

    try:
        # host.docker.internalが使える場合はそれを優先
        return socket.gethostbyname("host.docker.internal")
    except socket.gaierror:
        # 使えない場合はデフォルトゲートウェイ（通常はホスト）を試みる
        import subprocess
        try:
            route = subprocess.check_output(["ip", "route"]).decode()
            for line in route.splitlines():
                if "default via" in line:
                    return line.split()[2]
        except Exception:
            pass
    return "127.0.0.1"
