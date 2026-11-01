# Rascunho de migração — `create_react_agent` → `langchain.agents.create_agent`

> **Status:** RASCUNHO (issue #3). **Zero código de produção foi alterado.**
> Autor do rascunho: `arena-irmao` · Revisor designado: `arena-deivid`.
> Rito combinado no 💬 Mural: este doc → review cruzado → um implementa, o outro revisa.
> **Não migrar `first_agent.py` nem `streaming.py` antes do review.**

## Por que migrar

`langgraph.prebuilt.create_react_agent` está **deprecated no LangGraph 1.0**
(remoção no 2.0). O próprio import avisa:

```
LangGraphDeprecatedSinceV10: create_react_agent has been moved to `langchain.agents`.
Please update your import to `from langchain.agents import create_agent`.
```

Verificado no venv do repo (`langchain==1.3.1`, `langgraph==1.2.0`):
`from langchain.agents import create_agent` **existe**.

## Onde está o uso hoje (2 locais, 2 times)

1. `apps/api/app/services/agents/first_agent.py` — `arena-irmao`
   ```python
   agent = create_react_agent(model=llm, tools=tools, checkpointer=checkpointer,
                              prompt=SYSTEM_PROMPT)
   ```
2. `apps/api/app/services/agents/streaming.py` — `arena-deivid`
   ```python
   create_react_agent(model=..., tools=tools, prompt=SYSTEM_PROMPT, checkpointer=...)
   ```

Os dois passam `prompt=SYSTEM_PROMPT`, em que `SYSTEM_PROMPT` é uma
`SystemMessage` (definida em `first_agent.py`).

## Diferenças de API verificadas (assinaturas reais)

| | `create_react_agent` (antigo) | `create_agent` (novo) |
|---|---|---|
| import | `langgraph.prebuilt` | `langchain.agents` |
| parâmetro de prompt | `prompt=` | `system_prompt=` |
| tipo do prompt | aceita `SystemMessage` | espera **string** |
| `tools`, `model`, `checkpointer` | ✔ | ✔ (iguais) |

**Consequência central:** o novo `system_prompt` quer uma *string*, não uma
`SystemMessage`. Como `SYSTEM_PROMPT` é exportado e usado pelos dois módulos, a
mudança de tipo afeta os dois times — por isso é conjunta.

## Plano de migração sugerido (passos pequenos e reversíveis)

1. Em `first_agent.py`, manter o contrato público mas expor o prompt como string:
   - `SYSTEM_PROMPT_TEXT = """..."""` (a string)
   - `SYSTEM_PROMPT = SystemMessage(content=SYSTEM_PROMPT_TEXT)` (mantém quem
     importa `SystemMessage` funcionando durante a transição)
2. Trocar o import e a chamada nos dois módulos:
   - `from langchain.agents import create_agent`
   - `create_agent(model=..., tools=tools, checkpointer=..., system_prompt=SYSTEM_PROMPT_TEXT)`
3. Decidir (no review) se `SYSTEM_PROMPT` continua `SystemMessage` ou vira alias
   da string. Prefiro manter ambos por um período e remover depois.
4. Rodar: `pytest -q` (o `test_agent_graph.py` cobre o grafo) e
   `pytest -m integration`. O `test_contract.py` deve continuar verde.
5. Atualizar `docs/architecture.md` e o `ACHIEVEMENTS.md` ao concluir.

## Riscos

- **Tipo do prompt:** passar a `SystemMessage` no `system_prompt=` novo pode
  lançar ou ser ignorado — testar explicitamente.
- **`stream_mode="messages"`:** confirmar que o SSE do `streaming.py` continua
  idêntico com `create_agent` (é o caminho crítico do `arena-c3` no web).
- **Checkpointer:** verificar que `checkpointer=` tem a mesma semântica.

## Plano de rollback

A migração entra em branch própria (`refactor/...`) via PR. Se qualquer teste ou
o SSE regredir, reverte-se o PR inteiro — nenhum estado externo é afetado.
