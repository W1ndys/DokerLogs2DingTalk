import docker


def get_container_logs(container_name, num_lines):
    client = docker.from_env()
    try:
        container = client.containers.get(container_name)
        logs = container.logs(tail=num_lines)
        return logs.decode("utf-8")
    except docker.errors.NotFound:
        return f"容器 '{container_name}' 不存在."
    except Exception as e:
        return str(e)


# 示例用法
container_name = "napcat"
num_lines = 10
print(get_container_logs(container_name, num_lines))