# Dashboard Meta Ads · Connectabil

Dashboard das campanhas de Meta Ads da Connectabil, protegido por senha e atualizado sozinho todo dia às 7h (horário de Brasília).

## Publicar no GitHub Pages

1. Crie um repositório novo no suellen-hub (por exemplo `dashboard-meta-ads`). Pode ser público: o conteúdo do `index.html` é criptografado e só abre com a senha.
2. Envie **todos** os arquivos e pastas deste pacote, inclusive a pasta oculta `.github`.
3. Em **Settings → Pages**, escolha "Deploy from a branch", branch `main`, pasta `/ (root)`.
4. Em **Settings → Secrets and variables → Actions → New repository secret**, cadastre:
   - `WINDSOR_API_KEY`: a chave da API do Windsor.ai (no painel do Windsor, em API Key).
   - `DASH_SENHA`: a senha do dashboard.
5. Em **Actions**, abra "Atualizar dashboard Meta Ads" e clique em **Run workflow** para testar. Se terminar em verde, o link do Pages já mostra os dados novos.

Depois disso, a atualização roda sozinha todo dia.

## Como funciona

- `scripts/atualizar.py` busca os últimos 90 dias das contas de Meta Ads no Windsor.ai, monta o dashboard e criptografa a página com a senha (AES-GCM).
- `scripts/dashboard.html` é o modelo visual. `scripts/senha.html` é a tela de senha.
- Os dados brutos não vão para o repositório (pasta `dados/` no `.gitignore`): os números só existem dentro do `index.html` criptografado.

## Atenção

- O plano do Windsor.ai precisa permitir acesso pela API. Se a conta estiver em teste (Trial), a atualização para quando o teste acabar.
- Para trocar a senha, altere o secret `DASH_SENHA` e rode o workflow de novo.
- Rodar localmente: `DASH_SENHA=suasenha WINDSOR_API_KEY=suachave python scripts/atualizar.py`
