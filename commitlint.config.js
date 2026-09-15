module.exports = {
  extends: ['@commitlint/config-conventional'],
  rules: {
    // 'sync' não faz parte do config-conventional, mas é o tipo exigido pelo
    // protocolo do AGENT_SYNC.md para commits de coordenação entre os times
    // (claim de tarefa, check-in, recados). Sem ele, todo commit `sync:` seria
    // rejeitado — e o protocolo manda usar exatamente essa mensagem.
    'type-enum': [
      2,
      'always',
      [
        'build',
        'chore',
        'ci',
        'docs',
        'feat',
        'fix',
        'perf',
        'refactor',
        'revert',
        'style',
        'sync',
        'test',
      ],
    ],
  },
};
