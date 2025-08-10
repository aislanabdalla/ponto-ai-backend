# Ponto-AI (MVP) – Controle de ponto com reconhecimento facial

> **Aviso**: Este é um MVP educacional. Antes de uso real, reforce LGPD, segurança, antifraude e audite todo o código.

## Backend (FastAPI)

### Requisitos
- Python 3.10+
- Internet no primeiro run (InsightFace baixa modelos)

### Instalação
```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```
A API sobe em `http://127.0.0.1:8000`. Documentação: `http://127.0.0.1:8000/docs`

### Fluxo básico
1. **Criar funcionário**: `POST /employees` com `name`, `selfie` (arquivo). Guarda embedding facial.
2. **Bater ponto**: `POST /punches` com `employee_id`, `selfie`, opcional `lat`/`lon`. Compara embedding.
3. **Listar**: `GET /employees`
4. **Exportar CSV**: `GET /punches/export.csv`

> Por padrão, `SIMILARITY_THRESHOLD=0.80` (mais alto = mais rígido). Ajuste via variável de ambiente.

### TODO para produção
- Anti-spoofing/liveness (ex.: detecção de piscar/movimento, modelos anti-spoofing).
- Geofencing e restrição por horário/escala.
- Multi-usuário com RBAC e logs de auditoria.
- Criptografia em repouso de embeddings e fotos; rotação de chaves.
- Política de retenção e base legal (LGPD).
- Tests e CI/CD; imagens Docker; Postgres gerenciado.

## Mobile (Flutter – skeleton)
> Estrutura mínima para capturar selfie e enviar ao backend.

### Como usar
1. Instale Flutter SDK.
2. Crie um projeto Flutter vazio: `flutter create mobile`
3. Substitua a pasta `mobile/lib` e o `mobile/pubspec.yaml` pelos deste repositório.
4. No arquivo `lib/screens/api.dart`, ajuste `baseUrl` para apontar para o backend.

### Dependências (em `pubspec.yaml`)
- camera
- http
- path_provider
- permission_handler

### Telas do MVP
- **Cadastro Facial**: tira selfie e chama `POST /employees`.
- **Bater Ponto**: tira selfie e chama `POST /punches` (envia lat/lon se disponíveis).
