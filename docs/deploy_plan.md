# Mentalcare 배포 플랜 (백엔드)

## 0. 기본 정보

- GCP Project ID: `sesac-2805khun`
- Region: `asia-northeast3`
- Artifact Registry Repo: `mentalcare-backend`
- Image URI:
  - `asia-northeast3-docker.pkg.dev/sesac-2805khun/mentalcare-backend/mentalcare-api:test`
- Local DB (docker-compose):
  - POSTGRES_DB: `mentalcare`
  - POSTGRES_USER: `mental_admin`

---

## 1. 로컬 도커 테스트 (무료)

```bash
docker-compose up --build
# 컨테이너 안
docker exec -it fastapi-app bash
alembic upgrade head
