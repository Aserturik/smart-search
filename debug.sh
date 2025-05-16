#!/bin/bash

echo "====== Verificando estado de los contenedores ======"
docker-compose ps

echo -e "\n====== Logs de RabbitMQ ======"
docker-compose logs --tail=50 rabbitmq

echo -e "\n====== Verificando plugins activos en RabbitMQ ======"
docker-compose exec rabbitmq rabbitmq-plugins list -e

echo -e "\n====== Verificando puertos abiertos en RabbitMQ ======"
docker-compose exec rabbitmq netstat -tln

echo -e "\n====== Verificando conectividad de red ======"
docker-compose exec front ping -c 3 rabbitmq

echo -e "\n====== Logs del front ======"
docker-compose logs --tail=50 front

echo -e "\n====== Logs del back ======"
docker-compose logs --tail=50 back 