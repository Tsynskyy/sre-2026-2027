# Задачи

## Запуск

```sh
docker run --name sre-tasks-db -d -p 127.0.0.1:5432:5432 -e POSTGRES_USER=tasks -e POSTGRES_PASSWORD=tasks -e POSTGRES_DB=tasks postgres:17
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
export DATABASE_URL=postgresql://tasks:tasks@127.0.0.1:5432/tasks
.venv/bin/python migrate.py
.venv/bin/python app.py
```

Открыть http://127.0.0.1:8000

Переменные окружения: `DATABASE_URL` обязательна, `HOST` по умолчанию `127.0.0.1`, `PORT` по умолчанию `8000`

## Запуск в minikube

```sh
minikube start --driver=docker --container-runtime=docker
eval $(minikube docker-env)
docker build -t sre-tasks:1 .
kubectl apply -f k8s/
kubectl get pods
minikube service app --url
```

## Логи в VictoriaLogs

```sh
kubectl port-forward svc/victoria-logs 9428:9428
```

Открыть http://127.0.0.1:9428/select/vmui/

## Метрики в VictoriaMetrics

Приложение отдает метрики на порту `9100` (`METRICS_PORT`), путь `/metrics`
PostgreSQL - через `postgres-exporter` на `9187`

```sh
helm repo add vm https://victoriametrics.github.io/helm-charts/
helm install vm vm/victoria-metrics-single -n monitoring --create-namespace -f k8s/monitoring/vm-values.yaml
kubectl port-forward svc/vm-victoria-metrics-single-server -n monitoring 8428:8428
```

Открыть http://127.0.0.1:8428/vmui/

## Пробер

`prober.py` - Deployment `prober` из `k8s/prober.yaml`
Каждые 10 секунд создает, закрывает и удаляет задачу через `PROBE_TARGET`
метрика `probe_total` на порту `9100`

Развертывание описано в [Отчет.md](Отчет.md)
