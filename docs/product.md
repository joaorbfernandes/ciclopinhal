# Produto — CICLOPINHALEND 2.0 (V1)

> Fonte de verdade: *CICLOPINHALEND 2.0 — Visão do Produto (V1)*, aprovada, consolidada com as decisões de
> produto aprovadas depois do M0.
> Este ficheiro reproduz os requisitos aprovados. As decisões em aberto, sem regra aprovada, estão na secção 7
> («Em aberto») e são decididas nas especificações (`docs/specs/`); não são requisitos até serem aprovadas.

## Estados dos requisitos

| Estado | Onde está | Significado |
| --- | --- | --- |
| Requisito aprovado da V1 | Secções 2 e 3, sem marca | Faz parte da V1 |
| Requisito aprovado da V1 — fatia posterior | Blocos marcados com «▸» | Faz parte da V1, mas é implementado numa fatia posterior; a especificação respetiva define quando e como |
| Preparação estrutural | Secção 4 | A estrutura suporta; a funcionalidade não é exigida na V1 |
| Capacidade futura planeada | Secção 5 | Não implementar na V1 |
| Decisão em aberto | Secção 7 | Não é requisito |

## 1. Objetivo

Plataforma web configurável para pequenos negócios, começando pela Ciclopinhal.

Permite gerir um website profissional, catálogo de produtos, marcas, categorias, imagens e conteúdos através de
um backoffice simples.

A plataforma deve poder adaptar-se a outros tipos de negócio e evoluir com novas funcionalidades, sem exigir uma
reestruturação significativa do sistema.

Âmbito atual: a V1 foca-se em produtos físicos. Instalações futuras poderão oferecer produtos, serviços ou ambos;
a gestão de serviços não faz parte da V1 (secção 5). A V1 não inclui multi-tenancy.

## 2. Requisitos confirmados — website público

### Homepage

- Conjunto controlado de secções predefinidas e configuráveis. Não existe um construtor de páginas totalmente
  livre.
- Elementos estruturais obrigatórios, que não podem ser ocultados: navegação, área principal de apresentação e
  rodapé.
- As restantes secções de conteúdo são opcionais e podem ser mostradas ou ocultadas, sem eliminar os dados
  associados, dentro dos controlos disponibilizados pela Configuração (secção 3).
- Conteúdos e apresentação configuráveis dentro do sistema de design aprovado.
- As secções disponíveis podem evoluir à medida que a plataforma ganha capacidades.
- Produtos em destaque, selecionados pelo Administrador da Plataforma.
- Marcas em destaque, selecionadas individualmente.
- Banners, imagens e conteúdos editáveis.
- Design responsivo, acessível e otimizado.

### Catálogo

- Listagem de produtos com imagem, nome e preço.
- Organização por categorias e marcas.
- Página de detalhe com descrição, preço e galeria de imagens.
- Preços normais e promocionais.

#### Regras de categoria e marca

Aplicam-se aos produtos físicos da V1, independentemente do suporte futuro a serviços.

- Todo o produto tem exatamente uma categoria, obrigatória.
- Todo o produto pode ter uma marca, opcional (zero ou uma).
- Categorias e marcas são conceitos distintos.
- As categorias são planas: a V1 não tem subcategorias nem gestão hierárquica de categorias.

#### Galeria de imagens do produto

- A galeria é ordenada.
- A primeira imagem adicionada passa automaticamente a imagem principal.
- A imagem principal é a que ocupa a posição 0. O modelo conceptual não tem um atributo separado de imagem
  principal.
- O Administrador da Plataforma pode designar outra imagem como principal; essa imagem passa para a posição 0 e
  todas as restantes imagens mantêm a sua ordem relativa.
- Ao remover a imagem principal, a imagem seguinte passa a principal, se existir.
- Um produto pode existir sem imagens: as imagens são opcionais na criação e depois dela (D7).
- Um produto sem imagens é válido e é público como qualquer outro produto. Remover todas as imagens não invalida
  nem elimina o produto.
- A listagem e a página de detalhe suportam produtos sem imagens. A apresentação pública desse caso é uma decisão
  de apresentação em aberto (D18, secção 7), não uma regra de domínio.

#### Regras do produto

> Aprovadas pelo proprietário em 2026-11-15, registadas na `docs/specs/002-m1-catalog-domain.md` (campo
> `Approval`). A parte restante de D12 (edição manual do slug; slug quando o nome muda) continua em aberto (secção 7).

**Nome e descrição (N1, N2)**

- O nome é obrigatório. Os espaços no início e no fim são removidos; o nome não pode ficar vazio e tem no máximo
  200 caracteres.
- A descrição é opcional e pode ficar vazia. Os espaços no início e no fim são removidos.

**Preços (P4)**

- O preço normal é obrigatório e superior a zero.
- O preço promocional é opcional; quando existe, é superior a zero e estritamente inferior ao preço normal.
- Cada preço tem no máximo duas casas decimais, avaliadas pelo valor numérico: 10,500 é aceite e equivale a 10,50.
  Um valor com mais casas decimais significativas (por exemplo 10,505) é rejeitado, nunca arredondado.
- Valor máximo de cada preço: 99 999 999,99.

**Endereço do produto — slug (D12, parte da V1 inicial)**

- O slug é gerado automaticamente a partir do nome, na criação do produto.
- Contém apenas letras minúsculas sem acentos (a–z), algarismos e hífenes. Os acentos são removidos
  («Ação» → «acao»); qualquer outra sequência de caracteres passa a um único hífen; não há hífenes iniciais ou
  finais.
- Tem no máximo 160 caracteres, incluindo o sufixo de desambiguação.
- Se o slug já existir, tenta-se o sufixo «-2» e depois «-3»; se os três estiverem ocupados, a criação é recusada.
- Um nome do qual não se consegue gerar um slug válido (por exemplo, só símbolos) é rejeitado.
- A edição manual do slug não faz parte destas regras (D12, secção 7).

### Navegação

- Menu principal com entradas configuráveis.
- Possibilidade de criar submenus, por exemplo, Produtos → Bicicletas → Estrada. Os submenus são entradas de
  navegação e não implicam categorias hierárquicas.
- O Administrador da Plataforma pode alterar nomes, destinos, ordem e visibilidade das entradas, dentro de uma
  estrutura predefinida pela Configuração.
- Possibilidade de ocultar entradas do menu sem eliminar os dados associados.
- Páginas institucionais e contactos.

### ▸ Contactos e redes sociais (requisito da V1 — fatia posterior)

Ligações a redes sociais, contacto geral por WhatsApp e contacto por WhatsApp em cada produto fazem parte da V1.
Os detalhes de implementação estão em aberto (D16, secção 7).

Ligações a redes sociais:

- O negócio pode configurar várias ligações a redes sociais, como Instagram, Facebook ou outras plataformas.
- Cada ligação tem um identificador de plataforma e um URL de destino.
- Só as ligações configuradas e válidas aparecem publicamente. Sem ligações, não há ícones vazios nem marcadores
  de posição.
- Não há integrações com APIs de redes sociais, sincronização nem autenticação.

Contacto por WhatsApp:

- O negócio pode configurar um número de WhatsApp. O número é configuração do negócio e não é repetido em cada
  produto.
- O website tem uma ação geral de contacto por WhatsApp.
- Cada página de detalhe de produto tem uma ação de contacto por WhatsApp que gera uma mensagem pré-preenchida
  com o nome do produto e o respetivo URL público. O cliente abre o WhatsApp e decide se envia a mensagem.
- As ações de WhatsApp ficam ocultas quando não existe um número válido configurado.
- Não é necessária a API do WhatsApp Business. O contacto por WhatsApp não introduz carrinho, checkout,
  encomendas online nem contas de clientes.

## 3. Requisitos confirmados — backoffice

### Perfis de administração

A administração distingue dois perfis de acesso, por instalação de negócio (não é um requisito de multi-tenancy).
São responsabilidades de acesso conceptuais: não implicam modelos de utilizador, aplicações de administração ou
bases de dados separados. Este documento não define modelos de dados, papéis técnicos nem mecanismos de
permissões; a solução técnica é decidida no marco do backoffice (M5 em `docs/architecture.md`), que deve preferir
os mecanismos de autenticação e permissões existentes do Django, sujeito à decisão sobre a tecnologia de
administração.

**Administrador de Configuração** (*Setup Administrator*): o proprietário ou operador da plataforma que prepara e
configura cada instalação. Define o que a plataforma permite ao Administrador da Plataforma gerir.

- Configura a identidade do negócio e os contactos, incluindo WhatsApp e ligações a redes sociais.
- Seleciona quais das capacidades já implementadas ficam disponíveis.
- Define a estrutura permitida do website e as secções configuráveis, ou seja, a configuração estrutural
  protegida.
- Gere os utilizadores administrativos e as suas permissões de acesso.
- Controla a configuração protegida, que os administradores de conteúdo não podem alterar.

**Administrador da Plataforma** (*Platform Administrator*): o proprietário do negócio ou gestor de conteúdos
autorizado, responsável pela operação corrente.

- Cria, edita e gere produtos.
- Gere categorias e marcas.
- Gere media e galerias de produtos.
- Edita textos, imagens e conteúdos da homepage.
- Seleciona produtos e marcas em destaque.
- Gere a navegação e a visibilidade das secções opcionais, dentro da estrutura permitida pela Configuração.
- Gere eventos, quando a capacidade estiver implementada e ativada (secção 5).

Restrições do Administrador da Plataforma:

- Não ativa nem desativa capacidades da plataforma.
- Não altera a configuração de setup protegida.
- Não gere utilizadores, papéis nem permissões.
- Não altera as regras estruturais do website nem definições de layout sem restrições.
- Não contorna regras de domínio, validação de dados nem autorização.

Regras comuns:

- Ativar uma capacidade é da Configuração; gerir o seu conteúdo é do Administrador da Plataforma.
- A estrutura obrigatória do website é protegida: o Administrador da Plataforma edita o conteúdo permitido, mas
  não remove elementos estruturais obrigatórios.
- As secções opcionais só podem ser mostradas ou ocultadas através dos controlos que a Configuração disponibiliza.
- Só se podem ativar capacidades suportadas pela implementação. A Configuração não pode desativar invariantes de
  domínio nem ativar funcionalidades não implementadas.
- Uma mesma pessoa pode ter os dois perfis.
- As restrições são aplicadas no servidor, em cada pedido; esconder elementos da interface não é suficiente.

A lista exata da configuração protegida e dos controlos disponibilizados pela Configuração está em aberto (D15,
secção 7).

### Produtos

- Criar, editar e eliminar produtos.
- Associar categoria, marca e imagens, segundo as regras de «Catálogo» (secção 2).
- Definir preços e promoções.
- Escolher imagem principal e ordenar a galeria.
- Selecionar produtos em destaque na homepage.
- Os produtos ficam visíveis imediatamente após serem criados, sem processo de publicação.

### Marcas

- Criar, editar e eliminar marcas, respeitando associações existentes.
- Definir nome, descrição e logótipo/imagem.
- Associar produtos a marcas.
- Selecionar individualmente quais as marcas apresentadas na homepage.
- Uma marca pode existir no catálogo sem aparecer na homepage.

### Categorias

- Criar, editar e organizar categorias, numa lista plana.
- Associar produtos às categorias.

### Media

- Gestão centralizada de imagens.
- Reutilização de imagens entre diferentes contextos, incluindo produtos, marcas e conteúdos.
- Suporte para imagem principal, galerias e logótipos.
- Cada área controla as suas associações e regras de utilização.
- Processamento adequado das imagens para diferentes dimensões e contextos.
- Proteção contra remoção indevida de imagens ainda utilizadas.

### Configuração

A configuração protegida do negócio e da estrutura do website é do Administrador de Configuração; o conteúdo
corrente e a gestão do menu, dentro da estrutura permitida, são do Administrador da Plataforma (ver «Perfis de
administração»).

- Identidade do negócio, logótipo, contactos e informações gerais.
- Conteúdos e visibilidade das secções da homepage.
- Gestão do menu público, submenus e respetivos destinos.
- Configuração dos destaques de produtos e marcas.

## 4. Preparação estrutural (a estrutura suporta; a funcionalidade não é exigida na V1)

- Filtros por categoria, marca, intervalo de preço e outros atributos futuros.
- Pesquisa, ordenação e paginação.

O que destes pontos entra na listagem da V1 é definido na especificação da listagem (P8).

## 5. Evolução futura — não implementar na V1

A arquitetura deve facilitar, sem os implementar:

- Novos filtros e atributos dos produtos.
- Pesquisa avançada.
- Serviços em vez de, ou em conjunto com, produtos (ver abaixo).
- Eventos (ver abaixo).
- Categorias hierárquicas, a reconsiderar numa versão futura.
- Carrinho de compras.
- Checkout e pagamentos online.
- Encomendas e contas de clientes.
- Gestão de stock.
- Integrações externas e APIs.
- Backoffice personalizado.

### Eventos

Capacidade planeada da plataforma; não faz parte da V1 e ainda não tem especificação. Um evento simples poderá
ter:

- Título e descrição.
- Início e fim opcional (data e hora).
- Local.
- Imagem opcional.
- URL externo opcional de informação ou inscrição.
- Visibilidade pública.

Não estão aprovados para a implementação inicial: inscrições internas, participantes, pagamentos e eventos
recorrentes.

### Serviços

- O conceito de catálogo deve permitir expandir para serviços no futuro.
- Produtos e serviços podem partilhar conceitos de apresentação, mas ter regras de domínio e persistência
  distintas.
- Não se assume que toda a entrada de catálogo tenha marca, galeria ao estilo de produto ou preço de venda fixo.
  As regras de categoria e marca da secção 2 aplicam-se aos produtos físicos da V1; o que se aplica aos serviços
  está em aberto (D17).
- Não se adicionam agora entidades ou tabelas de serviços, herança entre produtos e serviços, reservas nem
  multi-tenancy.

## 6. Princípios de construção

- Arquitetura modular com fronteiras e responsabilidades claras.
- Regras de negócio independentes, tanto quanto praticável, da interface administrativa e da apresentação.
- Desenvolvimento incremental orientado por especificações.
- Testes automatizados e validação de cada fluxo.
- Infraestrutura reproduzível, CI/CD e preparação para deploy.
- Performance, segurança e manutenção consideradas desde o início.
- Documentação simples, com mapas dos fluxos, dependências e localização do código relevante.

A prioridade é construir uma V1 funcional, simples e sustentável, mantendo a possibilidade de evolução sem
implementar complexidade prematuramente.

## 7. Regras de negócio a especificar

### Em aberto

Não são requisitos aprovados. Onde existe proposta técnica, ela só se torna regra quando aprovada na
especificação indicada.

| ID | Questão | Proposta atual | Antes de |
| --- | --- | --- | --- |
| D12 | Política de slug (URL do produto), parte restante: edição manual do slug e comportamento do slug quando o nome muda. (Formato e geração na criação: resolvidos, secção 2, «Regras do produto».) | Gerado uma vez a partir do nome; editável só na criação | Fatia de edição do produto |
| D18 | Apresentação pública de um produto sem imagens, na listagem e no detalhe. É uma decisão de apresentação, não uma regra de domínio | — | M4 |
| P3 | Eliminar uma marca com produtos associados: bloquear ou outro comportamento? | Bloquear | M2 |
| D4 | Eliminar um produto ou marca em destaque | Deixa de aparecer na homepage, sem bloquear a eliminação | M2 |
| P2 | Eliminar uma categoria com produtos associados, sabendo que cada produto exige uma categoria. (A hierarquia está resolvida: categorias planas.) | — | M2 |
| D14 | Limites de upload: tamanho máximo, dimensões máximas, formatos aceites | — | M3 |
| P8 | Listagem da V1: paginação, ordenação, navegação por categoria e marca | — | M4 |
| P7 | Nível de acessibilidade a cumprir | — | M4 |
| D13 | Edição simultânea do mesmo produto, homepage ou menu | Último a gravar prevalece nos produtos; homepage e menus bloqueados durante a gravação | M5 |
| D15 | Lista exata da configuração protegida (por exemplo, informações gerais do negócio) e dos controlos de estrutura, menu e visibilidade de secções que a Configuração disponibiliza ao Administrador da Plataforma. Mecanismo técnico (autenticação, grupos, permissões, interface) decidido no marco do backoffice | — | M5 |
| D8 | Lista de secções predefinidas da homepage e conteúdo editável de cada uma; número máximo de destaques | — | Segunda fatia |
| P5 | Estrutura predefinida do menu: profundidade máxima; tipos de destino permitidos | — | Segunda fatia |
| P6 | Que páginas institucionais existem e que conteúdo é editável no backoffice | — | Fatia própria |
| D16 | Contactos e redes sociais: formato e validação do número de WhatsApp; texto da mensagem pré-preenchida; identificadores de plataforma, validação dos URL e ordem de apresentação das ligações | — | Fatia própria |
| D17 | Serviços: âmbito, modelo de preço, uso de categoria e marca, galeria e reservas | — | Fora da V1 |

### Resolvidas desde o M0

| ID | Resolução | Registada em |
| --- | --- | --- |
| D7 (categoria e marca) | Categoria única e obrigatória; marca opcional | Secção 2, «Regras de categoria e marca» |
| D7 (imagens) | Um produto pode existir sem imagens; é válido e público. A apresentação sem imagem fica em D18 | Secção 2, «Galeria de imagens do produto» |
| P4 | Preço normal > 0; promocional opcional, > 0 e estritamente inferior; no máximo duas casas decimais pelo valor, rejeitando e nunca arredondando; máximo 99 999 999,99 | Secção 2, «Regras do produto» |
| D12 (formato e geração) | Slug gerado a partir do nome na criação: a–z, algarismos e hífenes, sem acentos, máximo 160 caracteres com sufixo; três tentativas (`-2`, `-3`); nome sem slug válido é rejeitado | Secção 2, «Regras do produto» |
| N1 | Nome obrigatório, sem espaços nas pontas, no máximo 200 caracteres | Secção 2, «Regras do produto» |
| N2 | Descrição opcional, pode ser vazia, sem espaços nas pontas | Secção 2, «Regras do produto» |
| P1 | A primeira imagem é a principal; o Administrador da Plataforma pode alterá-la | Secção 2, «Galeria de imagens do produto» |
| P2 (hierarquia) | Categorias planas na V1 | Secção 2, «Regras de categoria e marca» |
