# Fyde Jarvis — Roadmap de produto

O roadmap antigo de bootstrap foi substituído por etapas de evolução sobre a base existente.
A auditoria técnica e os critérios de aceite estão em [audit-2026-11.md](./audit-2026-11.md).

## Já existe no repositório (a validar ponta a ponta)
- [x] API FastAPI + agente LangGraph
- [x] Memória conversacional via checkpointer PostgreSQL
- [x] Tools básicas: horário, calculadora AST, clima e busca web
- [x] Cliente de voz Linux com Whisper, Piper e openWakeWord
- [x] Comandos locais limitados por parser/allowlist e confirmação
- [x] Integração GitHub com leitura e escrita opt-in (branch + PR)
- [x] Docker Compose para Postgres + API
- [ ] Validar stack completa com credenciais reais, microfone e deploy

## Etapa 0 — estabilizar o que já existe
- [ ] Revisar PR #9: migração `create_react_agent` → `create_agent` em coordenação entre os donos dos arquivos
- [ ] Revisar PR #7: templates de issue e PR
- [ ] Confirmar e concluir Chat UI/SSE já iniciada em `feat/arena-c3/chat-streaming`
- [ ] Executar CI, testes e smoke test ponta a ponta

## Etapa 1 — segurança e identidade de dispositivos
- [ ] Desabilitar/proteger `/agent/chat-test*` em produção
- [ ] Credencial de dispositivo revogável e vinculada ao usuário
- [ ] Isolamento de conversas por usuário/dispositivo
- [ ] Rate limiting, limites de payload e timeouts
- [ ] Testes de acesso anônimo e isolamento

## Etapa 2 — execução autônoma no CachyOS
- [ ] Persistência de jobs e eventos no PostgreSQL
- [ ] API autenticada para criar, consultar e cancelar jobs
- [ ] Worker local como serviço systemd de usuário
- [ ] Conexão de saída autenticada (sem abrir shell/porta pública no PC)
- [ ] Lease, heartbeat, retry limitado e idempotência
- [ ] Política local de ferramentas, diretórios e comandos permitidos
- [ ] Relatórios de progresso e artefatos

## Etapa 3 — Android voz + texto
- [ ] PWA responsiva e instalável no POCO
- [ ] Chat com streaming autenticado
- [ ] Captura de voz no Android e transcrição
- [ ] Respostas por TTS no dispositivo
- [ ] Painel de jobs: fila, execução, falha, conclusão e cancelamento
- [ ] Web Push com consentimento e fallback no app

## Etapa 4 — agente desenvolvedor
- [ ] Fluxos de trabalho GitHub com branch + PR
- [ ] Execução de testes em workspace autorizado
- [ ] Acompanhamento de CI e resumo dos resultados
- [ ] Confirmação explícita para merge, deploy, publicação e ações destrutivas

## Critérios de pronto da v1 autônoma
- Tarefa iniciada no celular continua após fechar o app ou reiniciar a API.
- Worker no PC não exige porta pública de entrada.
- Usuário recebe progresso e notificação de conclusão/falha.
- Nenhum endpoint de produção permite uso anônimo do agente.
- Ferramentas locais recusam comandos e caminhos fora da política.
- Escrita em repositórios ocorre em branch e PR; merge/deploy exige autorização.

