# Planeja — sistema de planejamento agregado

Aplicação web que encontra um plano de produção de menor custo por programação linear inteira mista. O modelo considera força de trabalho, contratações, demissões, produção normal, horas extras, subcontratação, estoque e pedidos pendentes.

## Executar

```bash
python3 -m pip install -r requirements.txt
python3 app.py
```

Acesse `http://localhost:8000`. O formulário abre com o exemplo do PowerPoint e permite alterar o horizonte de planejamento.

## Publicar no Render

O arquivo `render.yaml` contém a configuração necessária para publicar o sistema como um serviço web. No Render, crie um novo Blueprint conectado a este repositório. A plataforma instalará as dependências e iniciará o servidor usando a porta fornecida pelo ambiente.

## Testar

```bash
python3 -m unittest discover -s tests -v
```

O custo de material incide sobre a produção interna normal e em horas extras. O custo informado para subcontratação é tratado como o custo completo por peça terceirizada. Trabalhadores, contratações e demissões são inteiros; as demais quantidades são contínuas.
