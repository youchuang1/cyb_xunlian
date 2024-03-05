from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_http_methods
import paramiko
import json


def get_ip_address():

    ip_address = '112.111.32.112'
    return ip_address

def index(request):
    return render(request, 'index.html',{'ip':get_ip_address()})


# 镜像列表
docker_images_list = {
    '1': 'zhonghui-env/at-python-05-01-613a:desktop',
    '2': 'zhonghui-env/at-python-05-02-611a:desktop',
    '3': 'zhonghui-env/at-python-05-03-610a:desktop',
    '4': 'zhonghui-env/at-python-05-04-623a:desktop'
}

# SSH 连接参数
hostname = get_ip_address()
port = 22
username = 'root'
password = '2403'


# 函数：提取容器名和镜像名
def get_container_image_name(name, image_id, image_dict):
    image_tag = image_dict.get(image_id)
    if not image_tag:
        return None, None
    parts = image_tag.split('-')
    leix = '_'.join(parts[2:5])
    container_name = f"{name}_{leix}"
    return container_name, image_tag


# 函数：通过SSH执行命令并返回结果
def ssh_exec_command(ssh_client, command):
    stdin, stdout, stderr = ssh_client.exec_command(command)
    result = stdout.read().decode('utf-8').strip()
    error = stderr.read().decode('utf-8').strip()
    if error:
        raise Exception(f"Error executing command '{command}': {error}")
    return result


@require_http_methods(["POST"])
def add(request):
    name = request.POST.get('name')
    image_id = request.POST.get('category')
    container_name, image_tag = get_container_image_name(name, image_id, docker_images_list)
    if not container_name:
        return JsonResponse({'error': '无效的类别序号'}, status=400)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port, username, password)

    try:
        # 检查容器是否存在（不论运行状态）
        existing_container = ssh_exec_command(
            ssh, f"docker ps -a --filter 'name=^{container_name}$' --format '{{{{.Names}}}}'"
        )

        # 如果容器不存在，创建并启动容器
        if not existing_container:
            ssh_exec_command(ssh, f"docker run -d -p 6901 --name {container_name} {image_tag}")
        else:
            # 检查容器是否正在运行
            running_container = ssh_exec_command(
                ssh, f"docker ps --filter 'name=^{container_name}$' --format '{{{{.Names}}}}'"
            )
            # 如果容器存在但未运行，启动容器
            if not running_container:
                ssh_exec_command(ssh, f"docker start {container_name}")

        # 获取容器的端口映射信息
        container_info_json = ssh_exec_command(ssh, f"docker inspect {container_name}")
        container_info = json.loads(container_info_json)
        ports_info = container_info[0]['NetworkSettings']['Ports']

        # 提取端口号
        if '6901/tcp' in ports_info and ports_info['6901/tcp']:
            port_number = ports_info['6901/tcp'][0]['HostPort']
            return JsonResponse({'port': port_number})
        else:
            return JsonResponse({'error': '端口未启用'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        ssh.close()


# 添加重启容器的视图
@require_http_methods(["POST"])
def restar(request):
    name = request.POST.get('name')
    image_id = request.POST.get('category')
    print(name, image_id)
    container_name, _ = get_container_image_name(name, image_id, docker_images_list)
    if not container_name:
        return JsonResponse({'error': '无效的类别序号'}, status=400)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port, username, password)

    try:
        # 重启容器
        ssh_exec_command(ssh, f"docker restart {container_name}")

        # 获取容器的端口映射信息
        container_info_json = ssh_exec_command(ssh, f"docker inspect {container_name}")
        container_info = json.loads(container_info_json)
        ports_info = container_info[0]['NetworkSettings']['Ports']

        # 提取端口号
        if '6901/tcp' in ports_info and ports_info['6901/tcp']:
            port_number = ports_info['6901/tcp'][0]['HostPort']
            return JsonResponse({'message': f'容器 {container_name} 已重启', 'port': port_number})
        else:
            return JsonResponse({'error': '容器端口未启用'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        ssh.close()


# 添加重置容器的视图
@require_http_methods(["POST"])
def reset(request):
    name = request.POST.get('name')
    image_id = request.POST.get('category')

    container_name, image_tag = get_container_image_name(name, image_id, docker_images_list)
    if not container_name:
        return JsonResponse({'error': '无效的类别序号'}, status=400)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port, username, password)

    try:
        # 停止并删除现有容器
        ssh_exec_command(ssh, f"docker stop {container_name}")
        ssh_exec_command(ssh, f"docker rm {container_name}")

        # 重新创建并启动容器，这里假设您想要绑定到一个新的随机端口
        ssh_exec_command(ssh, f"docker run -d -p 0:6901 --name {container_name} {image_tag}")

        # 重新获取端口映射信息
        container_info_json = ssh_exec_command(ssh, f"docker inspect {container_name}")
        container_info = json.loads(container_info_json)
        ports_info = container_info[0]['NetworkSettings']['Ports']

        # 提取新的端口号
        if '6901/tcp' in ports_info and ports_info['6901/tcp']:
            new_port_number = ports_info['6901/tcp'][0]['HostPort']
            return JsonResponse({'port': new_port_number})
        else:
            return JsonResponse({'error': '新容器端口未启用'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        ssh.close()


# 停止容器运行视图
@require_http_methods(["POST"])
def stop(request):
    name = request.POST.get('name')
    image_id = request.POST.get('category')
    container_name, _ = get_container_image_name(name, image_id, docker_images_list)
    if not container_name:
        return JsonResponse({'error': '无效的类别序号'}, status=400)

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    ssh.connect(hostname, port, username, password)

    try:
        # 停止容器
        ssh_exec_command(ssh, f"docker stop {container_name}")

        # 验证容器是否已停止
        stopped_container = ssh_exec_command(
            ssh, f"docker ps -a --filter 'name=^{container_name}$' --format '{{{{.Names}}}}'"
        )
        if stopped_container:
            return JsonResponse({'message': f'容器 {container_name} 已停止'})
        else:
            return JsonResponse({'error': '容器未能停止'}, status=404)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        ssh.close()

