# 使用Python 3.11官方镜像作为基础镜像
FROM python:3.11

# 设置环境变量，确保Python输出直接打印到控制台，不会被缓存
ENV PYTHONUNBUFFERED 1

# 在容器内部创建/app目录，并将其设置为工作目录
WORKDIR /app

# 将项目的requirements.txt文件复制到容器中
COPY requirements.txt /app/

# 使用pip安装requirements.txt中列出的所有依赖
RUN pip install --no-cache-dir -r requirements.txt -i http://pypi.douban.com/simple/ --trusted-host pypi.douban.com

# 将当前目录下的所有文件复制到容器的/app目录下
COPY . /app/

# 暴露容器的8000端口
EXPOSE 8000

# 设置容器启动时执行的命令，这里使用gunicorn作为WSGI服务器
# 替换xnj.wsgi:application为您实际的WSGI应用程序模块路径
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
