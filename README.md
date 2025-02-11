# Video Processing Lambda Functions

Este repositório contém o código das funções Lambda utilizadas no sistema de processamento de vídeos. O sistema permite que usuários façam upload de vídeos e recebam um arquivo ZIP contendo os frames extraídos.

## Arquitetura

O sistema é composto por três funções Lambda:

1. **Upload Handler**: Gerencia o processo de upload de vídeos
   - Gera URLs pré-assinadas para upload no S3
   - Registra metadados no DynamoDB
   - Envia mensagem para SQS para processamento

2. **Video Processor**: Processa os vídeos
   - Extrai frames dos vídeos usando OpenCV
   - Cria arquivo ZIP com os frames
   - Atualiza status no DynamoDB
   - Envia notificações via SNS

3. **Notification Handler**: Gerencia notificações
   - Recebe eventos do SNS
   - Busca informações do usuário no Cognito
   - Envia emails via SES

## Estrutura do Projeto

```
.
├── README.md
├── build.sh
├── run_tests.sh
├── pytest.ini
└── lambda/
    ├── upload_handler/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   ├── src/
    │   │   └── main.py
    │   └── tests/
    │       └── test_upload_handler.py
    ├── video_processor/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   ├── src/
    │   │   ├── main.py
    │   │   └── utils/
    │   │       ├── __init__.py
    │   │       ├── video.py
    │   │       └── storage.py
    │   └── tests/
    │       ├── test_video_processor.py
    │       └── test_storage.py
    └── notification_handler/
        ├── Dockerfile
        ├── requirements.txt
        ├── src/
        │   └── main.py
        └── tests/
            └── test_notification_handler.py
```

## Pré-requisitos

- Python 3.9+
- Docker
- AWS CLI configurado
- pytest e pytest-cov para testes
- Acesso a uma conta AWS com permissões para:
  - Lambda
  - ECR
  - S3
  - DynamoDB
  - SQS
  - SNS
  - SES
  - Cognito

## Instalação e Deploy

1. Clone o repositório:
```bash
git clone https://github.com/seu-usuario/video-processing-lambdas.git
cd video-processing-lambdas
```

2. Instale as dependências para desenvolvimento local:
```bash
# Para cada função Lambda
cd lambda/[função]/
pip install -r requirements.txt
```

3. Configure as variáveis de ambiente no script de build:
```bash
vim build.sh
# Ajuste AWS_REGION e ECR_REPOSITORY conforme necessário
```

4. Execute o script de build:
```bash
chmod +x build.sh
./build.sh
```

## Testes

O projeto utiliza pytest para testes unitários e de integração.

### Estrutura dos Testes

Cada função Lambda possui seus próprios testes:
- Testes unitários para cada componente
- Testes de integração para fluxos completos
- Mocks para serviços AWS
- Fixtures reutilizáveis
- Relatórios de cobertura de código

### Executando os Testes

1. Apenas testes unitários:
```bash
./run_tests.sh
```

2. Com testes de integração:
```bash
RUN_INTEGRATION_TESTS=true ./run_tests.sh
```

3. Testando uma função específica:
```bash
cd lambda/[função]/
python -m pytest tests/ -v --cov=src
```

### Tipos de Testes

1. **Upload Handler Tests**:
   - Geração de URLs pré-assinadas
   - Validação de requisições
   - Integração com S3 e DynamoDB
   - Tratamento de erros

2. **Video Processor Tests**:
   - Processamento de frames
   - Criação de arquivos ZIP
   - Manipulação de arquivos temporários
   - Integração com serviços AWS

3. **Notification Handler Tests**:
   - Envio de emails
   - Templates de notificação
   - Integração com Cognito e SES
   - Tratamento de falhas

### Cobertura de Testes

O projeto utiliza pytest-cov para gerar relatórios de cobertura. Configure os limites mínimos no arquivo `.coveragerc`:

```ini
[report]
exclude_lines =
    pragma: no cover
    def __repr__
fail_under = 80
```

## Variáveis de Ambiente

Cada função Lambda requer diferentes variáveis de ambiente:

### Upload Handler
- `INPUT_BUCKET`: Nome do bucket S3 para uploads
- `DYNAMODB_TABLE`: Nome da tabela DynamoDB
- `SQS_QUEUE_URL`: URL da fila SQS

### Video Processor
- `INPUT_BUCKET`: Nome do bucket S3 para vídeos
- `OUTPUT_BUCKET`: Nome do bucket S3 para frames
- `DYNAMODB_TABLE`: Nome da tabela DynamoDB
- `SNS_TOPIC_ARN`: ARN do tópico SNS

### Notification Handler
- `COGNITO_USER_POOL_ID`: ID do User Pool do Cognito
- `SENDER_EMAIL`: Email configurado no SES para envio

## CI/CD

O repositório inclui:
- Script de build (`build.sh`) para Docker
- Script de testes (`run_tests.sh`)
- Configuração de testes (`pytest.ini`)
- Relatórios de cobertura (`.coveragerc`)

## Links Úteis

- [Infraestrutura como Código](https://github.com/seu-usuario/video-processing-infrastructure)