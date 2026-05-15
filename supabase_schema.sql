-- ============================================================
-- GRILLATO SYSTEM - Schema Completo Supabase
-- ERP Hamburgueria - 11 Módulos Integrados
-- ============================================================

-- 0. EXTENSÕES
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- 1. CONFIGURAÇÕES DO SISTEMA
-- ============================================================
CREATE TABLE IF NOT EXISTS configuracoes (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  chave TEXT UNIQUE NOT NULL,
  valor JSONB NOT NULL,
  descricao TEXT,
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 2. FORNECEDORES
-- ============================================================
CREATE TABLE IF NOT EXISTS fornecedores (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nome TEXT NOT NULL,
  contato TEXT,
  telefone TEXT,
  email TEXT,
  endereco TEXT,
  observacoes TEXT,
  ativo BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 3. CATEGORIAS DE INSUMOS
-- ============================================================
CREATE TABLE IF NOT EXISTS categorias_insumo (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nome TEXT UNIQUE NOT NULL,
  descricao TEXT
);

-- ============================================================
-- 4. INSUMOS (ingredientes, embalagens, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS insumos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nome TEXT NOT NULL,
  categoria_id UUID REFERENCES categorias_insumo(id),
  unidade_compra TEXT NOT NULL,          -- "kg", "unid", "litro", "pacote"
  unidade_uso TEXT NOT NULL,             -- "g", "ml", "unid"
  fator_conversao NUMERIC NOT NULL DEFAULT 1000,  -- 1kg = 1000g
  custo_unitario NUMERIC(10,4) DEFAULT 0, -- custo por unidade_uso (ex: R$/g)
  estoque_atual NUMERIC(10,3) DEFAULT 0,  -- em unidade_compra
  estoque_minimo NUMERIC(10,3) DEFAULT 0,
  fornecedor_principal_id UUID REFERENCES fornecedores(id),
  ativo BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 5. CATEGORIAS DE PRODUTO (Lanches, Bebidas, Combos, etc.)
-- ============================================================
CREATE TABLE IF NOT EXISTS categorias_produto (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nome TEXT UNIQUE NOT NULL,
  descricao TEXT
);

-- ============================================================
-- 6. PRODUTOS DO CARDÁPIO
-- ============================================================
CREATE TABLE IF NOT EXISTS produtos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nome TEXT NOT NULL,
  categoria_id UUID REFERENCES categorias_produto(id),
  preco_venda NUMERIC(10,2) NOT NULL,
  descricao TEXT,
  foto_url TEXT,
  ativo BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 7. FICHAS TÉCNICAS (ingredientes por produto + gramaturas)
-- ============================================================
CREATE TABLE IF NOT EXISTS fichas_tecnicas (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  produto_id UUID NOT NULL REFERENCES produtos(id) ON DELETE CASCADE,
  insumo_id UUID NOT NULL REFERENCES insumos(id),
  quantidade NUMERIC(10,4) NOT NULL,     -- em unidade_uso do insumo
  modo_preparo TEXT,
  ordem INT DEFAULT 0,
  UNIQUE(produto_id, insumo_id)
);

-- ============================================================
-- 8. NOTAS FISCAIS (cabeçalho)
-- ============================================================
CREATE TABLE IF NOT EXISTS notas_fiscais (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  numero_nf TEXT,
  fornecedor_id UUID REFERENCES fornecedores(id),
  data_emissao DATE NOT NULL,
  valor_total NUMERIC(10,2) NOT NULL,
  observacoes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 9. ITENS DA NOTA FISCAL
-- ============================================================
CREATE TABLE IF NOT EXISTS itens_nota_fiscal (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nota_fiscal_id UUID NOT NULL REFERENCES notas_fiscais(id) ON DELETE CASCADE,
  insumo_id UUID NOT NULL REFERENCES insumos(id),
  quantidade NUMERIC(10,3) NOT NULL,     -- em unidade_compra
  valor_unitario NUMERIC(10,4) NOT NULL, -- preço por unidade_compra
  valor_total NUMERIC(10,2) NOT NULL
);

-- ============================================================
-- 10. MOVIMENTAÇÕES DE ESTOQUE
-- ============================================================
CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  insumo_id UUID NOT NULL REFERENCES insumos(id),
  tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida_venda', 'saida_perda', 'ajuste', 'inventario')),
  quantidade NUMERIC(10,3) NOT NULL,     -- positivo = entrada, negativo = saída
  saldo_apos NUMERIC(10,3) NOT NULL,
  referencia_id UUID,                    -- ID da NF, pedido, etc.
  referencia_tipo TEXT,                  -- 'nota_fiscal', 'pedido', 'manual'
  observacao TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 11. CUSTOS FIXOS
-- ============================================================
CREATE TABLE IF NOT EXISTS custos_fixos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  nome TEXT NOT NULL,
  valor NUMERIC(10,2) NOT NULL,
  categoria TEXT,                        -- 'aluguel', 'funcionario', 'plataforma', 'energia', etc.
  recorrencia TEXT DEFAULT 'mensal',     -- 'mensal', 'semanal', 'diario'
  ativo BOOLEAN DEFAULT true,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 12. PEDIDOS / VENDAS
-- ============================================================
CREATE TABLE IF NOT EXISTS pedidos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  numero_pedido TEXT,
  data_pedido TIMESTAMPTZ DEFAULT now(),
  canal TEXT DEFAULT 'balcao',           -- 'ifood', 'anota_ai', 'whatsapp', 'balcao', 'direto'
  subtotal NUMERIC(10,2) NOT NULL,
  taxa_entrega NUMERIC(10,2) DEFAULT 0,
  taxa_plataforma NUMERIC(10,2) DEFAULT 0,
  desconto NUMERIC(10,2) DEFAULT 0,
  total NUMERIC(10,2) NOT NULL,
  status TEXT DEFAULT 'concluido',
  observacoes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 13. ITENS DO PEDIDO
-- ============================================================
CREATE TABLE IF NOT EXISTS itens_pedido (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  pedido_id UUID NOT NULL REFERENCES pedidos(id) ON DELETE CASCADE,
  produto_id UUID NOT NULL REFERENCES produtos(id),
  quantidade INT NOT NULL DEFAULT 1,
  preco_unitario NUMERIC(10,2) NOT NULL,
  preco_total NUMERIC(10,2) NOT NULL,
  observacoes TEXT
);

-- ============================================================
-- 14. FECHAMENTO DIÁRIO (caixa/runway)
-- ============================================================
CREATE TABLE IF NOT EXISTS fechamentos_diarios (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  data DATE UNIQUE NOT NULL,
  faturamento_bruto NUMERIC(10,2) DEFAULT 0,
  total_pedidos INT DEFAULT 0,
  pedidos_direto INT DEFAULT 0,
  pedidos_ifood INT DEFAULT 0,
  pedidos_outros INT DEFAULT 0,
  custo_insumos NUMERIC(10,2) DEFAULT 0,
  custo_fixo_dia NUMERIC(10,2) DEFAULT 0,
  taxas_plataforma NUMERIC(10,2) DEFAULT 0,
  lucro_bruto NUMERIC(10,2) DEFAULT 0,
  caixa_apos NUMERIC(10,2),
  observacoes TEXT,
  created_at TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 15. HISTÓRICO DE PREÇOS (radar inflação)
-- ============================================================
CREATE TABLE IF NOT EXISTS historico_precos (
  id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  insumo_id UUID NOT NULL REFERENCES insumos(id),
  preco_anterior NUMERIC(10,4),
  preco_novo NUMERIC(10,4) NOT NULL,
  variacao_pct NUMERIC(6,2),
  fonte TEXT,                            -- 'nota_fiscal', 'manual', 'cotacao'
  data_registro TIMESTAMPTZ DEFAULT now()
);

-- ============================================================
-- 16. VIEW: CMV POR PRODUTO (calculado automaticamente)
-- ============================================================
CREATE OR REPLACE VIEW vw_cmv_produtos AS
SELECT
  p.id AS produto_id,
  p.nome,
  p.preco_venda,
  COALESCE(SUM(ft.quantidade * i.custo_unitario), 0) AS custo_total,
  p.preco_venda - COALESCE(SUM(ft.quantidade * i.custo_unitario), 0) AS lucro,
  CASE
    WHEN p.preco_venda > 0
    THEN ROUND((COALESCE(SUM(ft.quantidade * i.custo_unitario), 0) / p.preco_venda) * 100, 1)
    ELSE 0
  END AS cmv_pct
FROM produtos p
LEFT JOIN fichas_tecnicas ft ON ft.produto_id = p.id
LEFT JOIN insumos i ON i.id = ft.insumo_id
WHERE p.ativo = true
GROUP BY p.id, p.nome, p.preco_venda;

-- ============================================================
-- 17. VIEW: ESTOQUE COM ALERTAS
-- ============================================================
CREATE OR REPLACE VIEW vw_estoque_alertas AS
SELECT
  i.id,
  i.nome,
  ci.nome AS categoria,
  i.estoque_atual,
  i.estoque_minimo,
  i.unidade_compra,
  i.custo_unitario,
  CASE
    WHEN i.estoque_atual <= 0 THEN 'SEM_ESTOQUE'
    WHEN i.estoque_atual <= i.estoque_minimo THEN 'ABAIXO_MINIMO'
    WHEN i.estoque_atual <= i.estoque_minimo * 1.5 THEN 'ATENCAO'
    ELSE 'OK'
  END AS status_estoque,
  f.nome AS fornecedor
FROM insumos i
LEFT JOIN categorias_insumo ci ON ci.id = i.categoria_id
LEFT JOIN fornecedores f ON f.id = i.fornecedor_principal_id
WHERE i.ativo = true;

-- ============================================================
-- 18. VIEW: RESUMO FINANCEIRO DIÁRIO
-- ============================================================
CREATE OR REPLACE VIEW vw_resumo_financeiro AS
SELECT
  fd.data,
  fd.faturamento_bruto,
  fd.total_pedidos,
  fd.custo_insumos,
  fd.custo_fixo_dia,
  fd.taxas_plataforma,
  fd.lucro_bruto,
  fd.caixa_apos,
  CASE
    WHEN fd.faturamento_bruto > 0
    THEN ROUND((fd.custo_insumos / fd.faturamento_bruto) * 100, 1)
    ELSE 0
  END AS cmv_dia_pct,
  CASE
    WHEN fd.total_pedidos > 0
    THEN ROUND(fd.faturamento_bruto / fd.total_pedidos, 2)
    ELSE 0
  END AS ticket_medio
FROM fechamentos_diarios fd
ORDER BY fd.data DESC;

-- ============================================================
-- 19. FUNÇÃO: BAIXAR ESTOQUE AO REGISTRAR PEDIDO
-- ============================================================
CREATE OR REPLACE FUNCTION fn_baixar_estoque_pedido()
RETURNS TRIGGER AS $$
DECLARE
  rec RECORD;
  consumo NUMERIC;
  saldo_atual NUMERIC;
BEGIN
  -- Para cada item do pedido, buscar a ficha técnica
  FOR rec IN
    SELECT ft.insumo_id, ft.quantidade * NEW.quantidade AS total_consumo
    FROM fichas_tecnicas ft
    WHERE ft.produto_id = NEW.produto_id
  LOOP
    -- Converter de unidade_uso para unidade_compra
    SELECT i.estoque_atual, rec.total_consumo / i.fator_conversao
    INTO saldo_atual, consumo
    FROM insumos i WHERE i.id = rec.insumo_id;

    -- Atualizar estoque
    UPDATE insumos
    SET estoque_atual = GREATEST(0, estoque_atual - consumo),
        updated_at = now()
    WHERE id = rec.insumo_id;

    -- Registrar movimentação
    INSERT INTO movimentacoes_estoque (insumo_id, tipo, quantidade, saldo_apos, referencia_id, referencia_tipo)
    VALUES (
      rec.insumo_id,
      'saida_venda',
      -consumo,
      GREATEST(0, saldo_atual - consumo),
      NEW.pedido_id,
      'pedido'
    );
  END LOOP;

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_baixar_estoque
AFTER INSERT ON itens_pedido
FOR EACH ROW
EXECUTE FUNCTION fn_baixar_estoque_pedido();

-- ============================================================
-- 20. FUNÇÃO: ATUALIZAR ESTOQUE E PREÇO AO REGISTRAR NF
-- ============================================================
CREATE OR REPLACE FUNCTION fn_entrada_nota_fiscal()
RETURNS TRIGGER AS $$
DECLARE
  saldo_atual NUMERIC;
  custo_atual NUMERIC;
  novo_custo NUMERIC;
BEGIN
  -- Buscar dados atuais do insumo
  SELECT i.estoque_atual, i.custo_unitario
  INTO saldo_atual, custo_atual
  FROM insumos i WHERE i.id = NEW.insumo_id;

  -- Custo médio ponderado (por unidade_uso)
  IF saldo_atual > 0 AND custo_atual > 0 THEN
    novo_custo := ((saldo_atual * custo_atual * (SELECT fator_conversao FROM insumos WHERE id = NEW.insumo_id))
                   + (NEW.valor_total))
                  / ((saldo_atual + NEW.quantidade) * (SELECT fator_conversao FROM insumos WHERE id = NEW.insumo_id));
  ELSE
    novo_custo := NEW.valor_unitario / (SELECT fator_conversao FROM insumos WHERE id = NEW.insumo_id);
  END IF;

  -- Registrar preço antigo no histórico
  INSERT INTO historico_precos (insumo_id, preco_anterior, preco_novo, variacao_pct, fonte)
  VALUES (
    NEW.insumo_id,
    custo_atual,
    novo_custo,
    CASE WHEN custo_atual > 0 THEN ROUND(((novo_custo - custo_atual) / custo_atual) * 100, 2) ELSE 0 END,
    'nota_fiscal'
  );

  -- Atualizar estoque e custo
  UPDATE insumos
  SET estoque_atual = estoque_atual + NEW.quantidade,
      custo_unitario = novo_custo,
      updated_at = now()
  WHERE id = NEW.insumo_id;

  -- Registrar movimentação
  INSERT INTO movimentacoes_estoque (insumo_id, tipo, quantidade, saldo_apos, referencia_id, referencia_tipo)
  VALUES (
    NEW.insumo_id,
    'entrada',
    NEW.quantidade,
    saldo_atual + NEW.quantidade,
    NEW.nota_fiscal_id,
    'nota_fiscal'
  );

  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_entrada_nota_fiscal
AFTER INSERT ON itens_nota_fiscal
FOR EACH ROW
EXECUTE FUNCTION fn_entrada_nota_fiscal();

-- ============================================================
-- 21. DADOS INICIAIS: Categorias, Custos Fixos, Insumos base
-- ============================================================

-- Categorias de insumo
INSERT INTO categorias_insumo (nome, descricao) VALUES
  ('Proteinas', 'Carnes, frangos, etc.'),
  ('Laticinios', 'Queijos, cheddar, etc.'),
  ('Paes', 'Pão brioche, australiano, etc.'),
  ('Hortifruti', 'Verduras, legumes, batata'),
  ('Molhos', 'Molhos prontos e caseiros'),
  ('Embalagens', 'Caixas, sacolas, guardanapos'),
  ('Bebidas', 'Refrigerantes, sucos, agua')
ON CONFLICT (nome) DO NOTHING;

-- Categorias de produto
INSERT INTO categorias_produto (nome, descricao) VALUES
  ('Smash Burgers', 'Hambúrgueres smash'),
  ('Burgers Alto', 'Hambúrgueres tradicionais/gourmet'),
  ('Combos', 'Combos com bebida e/ou batata'),
  ('Acompanhamentos', 'Batata frita, onion rings, etc.'),
  ('Bebidas', 'Refrigerantes, sucos, milkshakes')
ON CONFLICT (nome) DO NOTHING;

-- Custos fixos da Grillato
INSERT INTO custos_fixos (nome, valor, categoria) VALUES
  ('Aluguel', 1500.00, 'aluguel'),
  ('Energia', 400.00, 'energia'),
  ('Internet', 120.00, 'internet'),
  ('Anota AI', 149.90, 'plataforma'),
  ('iFood mensalidade', 130.00, 'plataforma'),
  ('Funcionário 1', 1800.00, 'funcionario'),
  ('Funcionário 2', 1800.00, 'funcionario'),
  ('Parcela empréstimo', 1200.00, 'financeiro'),
  ('Contador', 300.00, 'administrativo'),
  ('Outros fixos', 500.00, 'outros');

-- ============================================================
-- 22. RLS (Row Level Security) - desabilitado por ora
-- ============================================================
-- Para o MVP mantemos sem RLS. Quando tiver multi-usuário, ativa.

-- ============================================================
-- 23. ÍNDICES
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_fichas_produto ON fichas_tecnicas(produto_id);
CREATE INDEX IF NOT EXISTS idx_fichas_insumo ON fichas_tecnicas(insumo_id);
CREATE INDEX IF NOT EXISTS idx_itens_nf_nota ON itens_nota_fiscal(nota_fiscal_id);
CREATE INDEX IF NOT EXISTS idx_itens_nf_insumo ON itens_nota_fiscal(insumo_id);
CREATE INDEX IF NOT EXISTS idx_mov_estoque_insumo ON movimentacoes_estoque(insumo_id);
CREATE INDEX IF NOT EXISTS idx_mov_estoque_data ON movimentacoes_estoque(created_at);
CREATE INDEX IF NOT EXISTS idx_pedidos_data ON pedidos(data_pedido);
CREATE INDEX IF NOT EXISTS idx_itens_pedido_pedido ON itens_pedido(pedido_id);
CREATE INDEX IF NOT EXISTS idx_itens_pedido_produto ON itens_pedido(produto_id);
CREATE INDEX IF NOT EXISTS idx_fechamentos_data ON fechamentos_diarios(data);
CREATE INDEX IF NOT EXISTS idx_historico_precos_insumo ON historico_precos(insumo_id);

