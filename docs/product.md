# Produto — CICLOPINHALEND 2.0 (V1)

> Fonte de verdade: *CICLOPINHALEND 2.0 — Visão do Produto (V1)*, aprovada.
> Este ficheiro reproduz os requisitos aprovados. Regras de detalhe ainda não aprovadas estão na secção 7 e são
> decididas nas especificações (`docs/specs/`).

## 1. Objetivo

Plataforma web configurável para pequenos negócios, começando pela Ciclopinhal.

Permite gerir um website profissional, catálogo de produtos, marcas, categorias, imagens e conteúdos através de
um backoffice simples.

A plataforma deve poder adaptar-se a outros tipos de negócio e evoluir com novas funcionalidades, sem exigir uma
reestruturação significativa do sistema.

## 2. Requisitos confirmados — website público

### Homepage

- Secções predefinidas, configuráveis e com possibilidade de serem ocultadas.
- Produtos em destaque, selecionados pelo administrador.
- Marcas em destaque, selecionadas individualmente.
- Banners, imagens e conteúdos editáveis.
- Design responsivo, acessível e otimizado.

### Catálogo

- Listagem de produtos com imagem, nome e preço.
- Organização por categorias e marcas.
- Página de detalhe com descrição, preço e galeria de imagens.
- Preços normais e promocionais.

### Navegação

- Menu principal com entradas configuráveis.
- Possibilidade de criar submenus, por exemplo, Produtos → Bicicletas → Estrada.
- O administrador pode alterar nomes, destinos, ordem e visibilidade das entradas, dentro de uma estrutura
  predefinida.
- Possibilidade de ocultar entradas e secções sem eliminar os dados associados.
- Páginas institucionais e contactos.

## 3. Requisitos confirmados — backoffice

### Produtos

- Criar, editar e eliminar produtos.
- Associar categorias, marcas e imagens.
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

- Criar, editar e organizar categorias.
- Associar produtos às categorias.
- Permitir organização hierárquica quando necessária.

### Media

- Gestão centralizada de imagens.
- Reutilização de imagens entre diferentes contextos, incluindo produtos, marcas e conteúdos.
- Suporte para imagem principal, galerias e logótipos.
- Cada área controla as suas associações e regras de utilização.
- Processamento adequado das imagens para diferentes dimensões e contextos.
- Proteção contra remoção indevida de imagens ainda utilizadas.

### Configuração

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
- Serviços em vez de, ou em conjunto com, produtos.
- Carrinho de compras.
- Checkout e pagamentos online.
- Encomendas e contas de clientes.
- Gestão de stock.
- Integrações externas e APIs.
- Backoffice personalizado.

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

Não são requisitos aprovados. Onde existe proposta técnica, ela só se torna regra quando aprovada na
especificação indicada.

| ID | Questão | Proposta atual | Antes de |
| --- | --- | --- | --- |
| D7 | Um produto tem uma ou várias categorias? A categoria é obrigatória? É obrigatória pelo menos uma imagem? | — | M1 |
| P1 | A imagem principal é escolhida explicitamente ou é a primeira da galeria? | — | M1 |
| P4 | Regras do preço promocional | Preço > 0; promocional > 0 e inferior ao preço normal | M1 |
| D12 | Política de slug (URL do produto) | Gerado uma vez a partir do nome; editável só na criação | M2 |
| P3 | Eliminar uma marca com produtos associados: bloquear ou outro comportamento? | Bloquear | M2 |
| D4 | Eliminar um produto ou marca em destaque | Deixa de aparecer na homepage, sem bloquear a eliminação | M2 |
| P2 | Hierarquia de categorias: profundidade máxima; eliminação de categorias com produtos ou subcategorias | — | M2 |
| D14 | Limites de upload: tamanho máximo, dimensões máximas, formatos aceites | — | M3 |
| P8 | Listagem da V1: paginação, ordenação, navegação por categoria e marca | — | M4 |
| P7 | Nível de acessibilidade a cumprir | — | M4 |
| D13 | Edição simultânea do mesmo produto, homepage ou menu | Último a gravar prevalece nos produtos; homepage e menus bloqueados durante a gravação | M5 |
| D8 | Lista de secções predefinidas da homepage e conteúdo editável de cada uma; número máximo de destaques | — | Segunda fatia |
| P5 | Estrutura predefinida do menu: profundidade máxima; tipos de destino permitidos | — | Segunda fatia |
| P6 | Que páginas institucionais existem e que conteúdo é editável no backoffice | — | Fatia própria |
