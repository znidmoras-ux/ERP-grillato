-- ============================================================
-- GRILLATO SYSTEM - Seed Data
-- Hamburgueria Smash Burger - Arapongas, PR
-- Compatível com schema supabase_schema.sql
-- ============================================================

-- Desabilitar triggers temporariamente para não disparar
-- baixa de estoque/atualização de preço durante o seed
ALTER TABLE itens_pedido DISABLE TRIGGER trg_baixar_estoque;
ALTER TABLE itens_nota_fiscal DISABLE TRIGGER trg_entrada_nota_fiscal;

-- ============================================================
-- 1. FORNECEDORES
-- ============================================================
INSERT INTO fornecedores (nome, contato, telefone, email, endereco, observacoes) VALUES
  ('Delly''s Distribuidora', 'Carlos', '(43) 3252-1100', 'vendas@dellys.com.br', 'Rod PR-445 km 12, Arapongas-PR', 'Entrega toda terça e sexta'),
  ('Frigorifico Arapongas', 'Marcos', '(43) 3275-3300', 'comercial@frigoarapongas.com.br', 'Av. Industrial 890, Arapongas-PR', 'Carnes e proteinas - pedido minimo R$200'),
  ('Distribuidora Norte PR', 'Ana', '(43) 3252-8800', 'pedidos@nortepr.com.br', 'R. Presidente Vargas 456, Londrina-PR', 'Molhos, laticinios, hortifruti'),
  ('Embalagens Express', 'Roberto', '(43) 99812-4455', 'contato@embalagensexpress.com.br', 'R. Tucunare 123, Arapongas-PR', 'Entrega em 24h para pedidos até 13h');

-- ============================================================
-- 2. INSUMOS (16 itens)
-- ============================================================
-- Precisamos dos IDs das categorias e fornecedores via subquery

-- Proteinas
INSERT INTO insumos (nome, categoria_id, unidade_compra, unidade_uso, fator_conversao, custo_unitario, estoque_atual, estoque_minimo, fornecedor_principal_id) VALUES
  ('Blend Smash 70g',
    (SELECT id FROM categorias_insumo WHERE nome = 'Proteinas'),
    'unid', 'unid', 1, 0.8500, 500, 200,
    (SELECT id FROM fornecedores WHERE nome = 'Frigorifico Arapongas')),
  ('Bacon Fatiado',
    (SELECT id FROM categorias_insumo WHERE nome = 'Proteinas'),
    'kg', 'g', 1000, 0.0450, 8, 3,
    (SELECT id FROM fornecedores WHERE nome = 'Frigorifico Arapongas'));

-- Paes
INSERT INTO insumos (nome, categoria_id, unidade_compra, unidade_uso, fator_conversao, custo_unitario, estoque_atual, estoque_minimo, fornecedor_principal_id) VALUES
  ('Pao Brioche',
    (SELECT id FROM categorias_insumo WHERE nome = 'Paes'),
    'unid', 'unid', 1, 1.2000, 300, 100,
    (SELECT id FROM fornecedores WHERE nome = 'Delly''s Distribuidora'));

-- Laticinios
INSERT INTO insumos (nome, categoria_id, unidade_compra, unidade_uso, fator_conversao, custo_unitario, estoque_atual, estoque_minimo, fornecedor_principal_id) VALUES
  ('Cheddar Fatiado',
    (SELECT id FROM categorias_insumo WHERE nome = 'Laticinios'),
    'kg', 'g', 1000, 0.0380, 6, 2,
    (SELECT id FROM fornecedores WHERE nome = 'Distribuidora Norte PR')),
  ('Mucarela Fatiada',
    (SELECT id FROM categorias_insumo WHERE nome = 'Laticinios'),
    'kg', 'g', 1000, 0.0320, 5, 2,
    (SELECT id FROM fornecedores WHERE nome = 'Distribuidora Norte PR'));

-- Molhos
INSERT INTO insumos (nome, categoria_id, unidade_compra, unidade_uso, fator_conversao, custo_unitario, estoque_atual, estoque_minimo, fornecedor_principal_id) VALUES
  ('Molho Especial Grillato',
    (SELECT id FROM categorias_insumo WHERE nome = 'Molhos'),
    'litro', 'ml', 1000, 0.0150, 4, 1,
    (SELECT id FROM fornecedores WHERE nome = 'Distribuidora Norte PR')),
  ('Ketchup',
    (SELECT id FROM categorias_insumo WHERE nome = 'Molhos'),
    'litro', 'ml', 1000, 0.0080, 3, 1,
    (SELECT id FROM fornecedores WHERE nome = 'Distribuidora Norte PR')),
  ('Maionese',
    (SELECT id FROM categorias_insumo WHERE nome = 'Molhos'),
    'litro', 'ml', 1000, 0.0120, 3, 1,
    (SELECT id FROM fornecedores WHERE nome = 'Distribuidora Norte PR'));

-- Hortifruti
INSERT INTO insumos (nome, categoria_id, unidade_compra, unidade_uso, fator_conversao, custo_unitario, estoque_atual, estoque_minimo, fornecedor_principal_id) VALUES
  ('Alface Crespa',
    (SELECT id FROM categorias_insumo WHERE nome = 'Hortifruti'),
    'unid', 'unid', 1, 4.0000, 10, 3,
    (SELECT id FROM fornecedores WHERE nome = 'Distribuidora Norte PR')),
  ('Tomate',
    (SELECT id FROM categorias_insumo WHERE nome = 'Hortifruti'),
    'kg', 'g', 1000, 0.0080, 5, 2,
    (SELECT id FROM fornecedores WHERE nome = 'Distribuidora Norte PR')),
  ('Cebola Caramelizada',
    (SELECT id FROM categorias_insumo WHERE nome = 'Hortifruti'),
    'kg', 'g', 1000, 0.0180, 3, 1,
    (SELECT id FROM fornecedores WHERE nome = 'Distribuidora Norte PR')),
  ('Batata Congelada',
    (SELECT id FROM categorias_insumo WHERE nome = 'Hortifruti'),
    'kg', 'g', 1000, 0.0120, 10, 4,
    (SELECT id FROM fornecedores WHERE nome = 'Delly''s Distribuidora'));

-- Embalagens
INSERT INTO insumos (nome, categoria_id, unidade_compra, unidade_uso, fator_conversao, custo_unitario, estoque_atual, estoque_minimo, fornecedor_principal_id) VALUES
  ('Caixa Burger',
    (SELECT id FROM categorias_insumo WHERE nome = 'Embalagens'),
    'unid', 'unid', 1, 0.4500, 400, 150,
    (SELECT id FROM fornecedores WHERE nome = 'Embalagens Express')),
  ('Copo 500ml',
    (SELECT id FROM categorias_insumo WHERE nome = 'Embalagens'),
    'unid', 'unid', 1, 0.3000, 200, 80,
    (SELECT id FROM fornecedores WHERE nome = 'Embalagens Express')),
  ('Guardanapo',
    (SELECT id FROM categorias_insumo WHERE nome = 'Embalagens'),
    'unid', 'unid', 1, 0.0200, 1000, 300,
    (SELECT id FROM fornecedores WHERE nome = 'Embalagens Express'));

-- Bebidas
INSERT INTO insumos (nome, categoria_id, unidade_compra, unidade_uso, fator_conversao, custo_unitario, estoque_atual, estoque_minimo, fornecedor_principal_id) VALUES
  ('Coca-Cola Lata 350ml',
    (SELECT id FROM categorias_insumo WHERE nome = 'Bebidas'),
    'unid', 'unid', 1, 3.5000, 48, 24,
    (SELECT id FROM fornecedores WHERE nome = 'Delly''s Distribuidora')),
  ('Guarana Lata 350ml',
    (SELECT id FROM categorias_insumo WHERE nome = 'Bebidas'),
    'unid', 'unid', 1, 3.2000, 36, 24,
    (SELECT id FROM fornecedores WHERE nome = 'Delly''s Distribuidora'));

-- ============================================================
-- 3. PRODUTOS DO CARDÁPIO (8 itens)
-- ============================================================
INSERT INTO produtos (nome, categoria_id, preco_venda, descricao) VALUES
  ('Smash Simples',
    (SELECT id FROM categorias_produto WHERE nome = 'Smash Burgers'),
    18.90, '1 smash 70g, cheddar, molho especial no pao brioche'),
  ('Smash Duplo',
    (SELECT id FROM categorias_produto WHERE nome = 'Smash Burgers'),
    24.90, '2 smash 70g, cheddar, molho especial no pao brioche'),
  ('Smash Bacon',
    (SELECT id FROM categorias_produto WHERE nome = 'Smash Burgers'),
    27.90, '2 smash 70g, cheddar, bacon crocante, molho especial'),
  ('Smash Especial Grillato',
    (SELECT id FROM categorias_produto WHERE nome = 'Smash Burgers'),
    29.90, '2 smash 70g, cheddar, bacon, cebola caramelizada, molho especial'),
  ('Combo Explosao',
    (SELECT id FROM categorias_produto WHERE nome = 'Combos'),
    39.90, 'Smash Duplo + Batata Frita + Refrigerante Lata'),
  ('Combo Simples',
    (SELECT id FROM categorias_produto WHERE nome = 'Combos'),
    29.90, 'Smash Simples + Refrigerante Lata'),
  ('Refrigerante Lata',
    (SELECT id FROM categorias_produto WHERE nome = 'Bebidas'),
    6.00, 'Coca-Cola ou Guarana 350ml'),
  ('Batata Frita',
    (SELECT id FROM categorias_produto WHERE nome = 'Acompanhamentos'),
    14.90, 'Porcao de batata frita crocante 200g');

-- ============================================================
-- 4. FICHAS TÉCNICAS
-- ============================================================

-- Smash Simples: 1 blend, 1 pao, 30g cheddar, 15ml molho, 1 caixa
INSERT INTO fichas_tecnicas (produto_id, insumo_id, quantidade, ordem) VALUES
  ((SELECT id FROM produtos WHERE nome = 'Smash Simples'),
   (SELECT id FROM insumos WHERE nome = 'Blend Smash 70g'), 1, 1),
  ((SELECT id FROM produtos WHERE nome = 'Smash Simples'),
   (SELECT id FROM insumos WHERE nome = 'Pao Brioche'), 1, 2),
  ((SELECT id FROM produtos WHERE nome = 'Smash Simples'),
   (SELECT id FROM insumos WHERE nome = 'Cheddar Fatiado'), 30, 3),
  ((SELECT id FROM produtos WHERE nome = 'Smash Simples'),
   (SELECT id FROM insumos WHERE nome = 'Molho Especial Grillato'), 15, 4),
  ((SELECT id FROM produtos WHERE nome = 'Smash Simples'),
   (SELECT id FROM insumos WHERE nome = 'Caixa Burger'), 1, 5);

-- Smash Duplo: 2 blend, 1 pao, 50g cheddar, 20ml molho, 1 caixa
INSERT INTO fichas_tecnicas (produto_id, insumo_id, quantidade, ordem) VALUES
  ((SELECT id FROM produtos WHERE nome = 'Smash Duplo'),
   (SELECT id FROM insumos WHERE nome = 'Blend Smash 70g'), 2, 1),
  ((SELECT id FROM produtos WHERE nome = 'Smash Duplo'),
   (SELECT id FROM insumos WHERE nome = 'Pao Brioche'), 1, 2),
  ((SELECT id FROM produtos WHERE nome = 'Smash Duplo'),
   (SELECT id FROM insumos WHERE nome = 'Cheddar Fatiado'), 50, 3),
  ((SELECT id FROM produtos WHERE nome = 'Smash Duplo'),
   (SELECT id FROM insumos WHERE nome = 'Molho Especial Grillato'), 20, 4),
  ((SELECT id FROM produtos WHERE nome = 'Smash Duplo'),
   (SELECT id FROM insumos WHERE nome = 'Caixa Burger'), 1, 5);

-- Smash Bacon: 2 blend, 1 pao, 40g cheddar, 30g bacon, 20ml molho, 1 caixa
INSERT INTO fichas_tecnicas (produto_id, insumo_id, quantidade, ordem) VALUES
  ((SELECT id FROM produtos WHERE nome = 'Smash Bacon'),
   (SELECT id FROM insumos WHERE nome = 'Blend Smash 70g'), 2, 1),
  ((SELECT id FROM produtos WHERE nome = 'Smash Bacon'),
   (SELECT id FROM insumos WHERE nome = 'Pao Brioche'), 1, 2),
  ((SELECT id FROM produtos WHERE nome = 'Smash Bacon'),
   (SELECT id FROM insumos WHERE nome = 'Cheddar Fatiado'), 40, 3),
  ((SELECT id FROM produtos WHERE nome = 'Smash Bacon'),
   (SELECT id FROM insumos WHERE nome = 'Bacon Fatiado'), 30, 4),
  ((SELECT id FROM produtos WHERE nome = 'Smash Bacon'),
   (SELECT id FROM insumos WHERE nome = 'Molho Especial Grillato'), 20, 5),
  ((SELECT id FROM produtos WHERE nome = 'Smash Bacon'),
   (SELECT id FROM insumos WHERE nome = 'Caixa Burger'), 1, 6);

-- Smash Especial Grillato: 2 blend, 1 pao, 50g cheddar, 30g bacon, 25ml molho, 20g cebola caram, 1 caixa
INSERT INTO fichas_tecnicas (produto_id, insumo_id, quantidade, ordem) VALUES
  ((SELECT id FROM produtos WHERE nome = 'Smash Especial Grillato'),
   (SELECT id FROM insumos WHERE nome = 'Blend Smash 70g'), 2, 1),
  ((SELECT id FROM produtos WHERE nome = 'Smash Especial Grillato'),
   (SELECT id FROM insumos WHERE nome = 'Pao Brioche'), 1, 2),
  ((SELECT id FROM produtos WHERE nome = 'Smash Especial Grillato'),
   (SELECT id FROM insumos WHERE nome = 'Cheddar Fatiado'), 50, 3),
  ((SELECT id FROM produtos WHERE nome = 'Smash Especial Grillato'),
   (SELECT id FROM insumos WHERE nome = 'Bacon Fatiado'), 30, 4),
  ((SELECT id FROM produtos WHERE nome = 'Smash Especial Grillato'),
   (SELECT id FROM insumos WHERE nome = 'Molho Especial Grillato'), 25, 5),
  ((SELECT id FROM produtos WHERE nome = 'Smash Especial Grillato'),
   (SELECT id FROM insumos WHERE nome = 'Cebola Caramelizada'), 20, 6),
  ((SELECT id FROM produtos WHERE nome = 'Smash Especial Grillato'),
   (SELECT id FROM insumos WHERE nome = 'Caixa Burger'), 1, 7);

-- Combo Explosao: same as Duplo + batata + refri
INSERT INTO fichas_tecnicas (produto_id, insumo_id, quantidade, ordem) VALUES
  ((SELECT id FROM produtos WHERE nome = 'Combo Explosao'),
   (SELECT id FROM insumos WHERE nome = 'Blend Smash 70g'), 2, 1),
  ((SELECT id FROM produtos WHERE nome = 'Combo Explosao'),
   (SELECT id FROM insumos WHERE nome = 'Pao Brioche'), 1, 2),
  ((SELECT id FROM produtos WHERE nome = 'Combo Explosao'),
   (SELECT id FROM insumos WHERE nome = 'Cheddar Fatiado'), 50, 3),
  ((SELECT id FROM produtos WHERE nome = 'Combo Explosao'),
   (SELECT id FROM insumos WHERE nome = 'Molho Especial Grillato'), 20, 4),
  ((SELECT id FROM produtos WHERE nome = 'Combo Explosao'),
   (SELECT id FROM insumos WHERE nome = 'Caixa Burger'), 1, 5),
  ((SELECT id FROM produtos WHERE nome = 'Combo Explosao'),
   (SELECT id FROM insumos WHERE nome = 'Batata Congelada'), 200, 6),
  ((SELECT id FROM produtos WHERE nome = 'Combo Explosao'),
   (SELECT id FROM insumos WHERE nome = 'Coca-Cola Lata 350ml'), 1, 7);

-- Combo Simples: Smash Simples + Refri
INSERT INTO fichas_tecnicas (produto_id, insumo_id, quantidade, ordem) VALUES
  ((SELECT id FROM produtos WHERE nome = 'Combo Simples'),
   (SELECT id FROM insumos WHERE nome = 'Blend Smash 70g'), 1, 1),
  ((SELECT id FROM produtos WHERE nome = 'Combo Simples'),
   (SELECT id FROM insumos WHERE nome = 'Pao Brioche'), 1, 2),
  ((SELECT id FROM produtos WHERE nome = 'Combo Simples'),
   (SELECT id FROM insumos WHERE nome = 'Cheddar Fatiado'), 30, 3),
  ((SELECT id FROM produtos WHERE nome = 'Combo Simples'),
   (SELECT id FROM insumos WHERE nome = 'Molho Especial Grillato'), 15, 4),
  ((SELECT id FROM produtos WHERE nome = 'Combo Simples'),
   (SELECT id FROM insumos WHERE nome = 'Caixa Burger'), 1, 5),
  ((SELECT id FROM produtos WHERE nome = 'Combo Simples'),
   (SELECT id FROM insumos WHERE nome = 'Coca-Cola Lata 350ml'), 1, 6);

-- Refrigerante Lata: 1 coca-cola (representativo)
INSERT INTO fichas_tecnicas (produto_id, insumo_id, quantidade, ordem) VALUES
  ((SELECT id FROM produtos WHERE nome = 'Refrigerante Lata'),
   (SELECT id FROM insumos WHERE nome = 'Coca-Cola Lata 350ml'), 1, 1);

-- Batata Frita: 200g batata congelada
INSERT INTO fichas_tecnicas (produto_id, insumo_id, quantidade, ordem) VALUES
  ((SELECT id FROM produtos WHERE nome = 'Batata Frita'),
   (SELECT id FROM insumos WHERE nome = 'Batata Congelada'), 200, 1);

-- ============================================================
-- 5. FECHAMENTOS DIÁRIOS — últimos 30 dias (pula domingos)
-- ============================================================
-- Data base: 2026-05-15, gerar de 2026-04-15 a 2026-05-15
-- Domingo = EXTRACT(DOW) = 0

DO $$
DECLARE
  d DATE;
  dow INT;
  fat NUMERIC;
  n_ped INT;
  custo_ins NUMERIC;
  custo_fix NUMERIC;
  taxas NUMERIC;
  ped_ifood INT;
  ped_direto INT;
  ped_outros INT;
  caixa NUMERIC := 8500.00; -- saldo inicial estimado
BEGIN
  d := DATE '2026-04-15';
  WHILE d <= DATE '2026-05-15' LOOP
    dow := EXTRACT(DOW FROM d);

    -- Pular domingos
    IF dow = 0 THEN
      d := d + 1;
      CONTINUE;
    END IF;

    -- Sexta (5) e Sabado (6) = dias fortes
    IF dow IN (5, 6) THEN
      n_ped := 30 + floor(random() * 8)::int;   -- 30-37 pedidos
      fat := n_ped * (30.0 + random() * 4.0);    -- ticket ~R$30-34
    ELSE
      n_ped := 22 + floor(random() * 7)::int;    -- 22-28 pedidos
      fat := n_ped * (27.0 + random() * 5.0);    -- ticket ~R$27-32
    END IF;

    fat := round(fat, 2);
    custo_ins := round(fat * (0.30 + random() * 0.05), 2);  -- 30-35% CMV
    custo_fix := round(350 + random() * 50, 2);              -- ~R$350-400/dia rateio
    taxas := round(fat * (0.08 + random() * 0.04), 2);       -- 8-12% taxas plataforma

    ped_ifood := round(n_ped * 0.55)::int;
    ped_direto := round(n_ped * 0.25)::int;
    ped_outros := n_ped - ped_ifood - ped_direto;

    caixa := caixa + fat - custo_ins - custo_fix - taxas;

    INSERT INTO fechamentos_diarios (
      data, faturamento_bruto, total_pedidos,
      pedidos_ifood, pedidos_direto, pedidos_outros,
      custo_insumos, custo_fixo_dia, taxas_plataforma,
      lucro_bruto, caixa_apos
    ) VALUES (
      d, fat, n_ped,
      ped_ifood, ped_direto, ped_outros,
      custo_ins, custo_fix, taxas,
      round(fat - custo_ins - custo_fix - taxas, 2),
      round(caixa, 2)
    );

    d := d + 1;
  END LOOP;
END $$;

-- ============================================================
-- 6. PEDIDOS — últimos 7 dias (~25/dia) com itens
-- ============================================================

DO $$
DECLARE
  d DATE;
  dow INT;
  n_ped INT;
  i INT;
  canal_val TEXT;
  hora_val TIMESTAMPTZ;
  rand_val NUMERIC;
  ped_id UUID;
  prod_id UUID;
  prod_preco NUMERIC;
  prod_nome TEXT;
  qtd INT;
  sub NUMERIC;
  n_itens INT;
  j INT;
  hora_h INT;
  hora_m INT;
  item_rand NUMERIC;

  -- Product arrays via temp table approach
  arr_prod_id UUID[];
  arr_prod_preco NUMERIC[];
  arr_prod_nome TEXT[];
  arr_prod_peso NUMERIC[]; -- probability weight
BEGIN
  -- Load products into arrays
  SELECT array_agg(id), array_agg(preco_venda), array_agg(nome)
  INTO arr_prod_id, arr_prod_preco, arr_prod_nome
  FROM produtos ORDER BY nome;

  -- Weight array for product selection (index matches sorted nome order):
  -- Batata Frita, Combo Explosao, Combo Simples, Refrigerante Lata,
  -- Smash Bacon, Smash Duplo, Smash Especial Grillato, Smash Simples
  -- Weights: 0.10, 0.12, 0.10, 0.08, 0.18, 0.20, 0.10, 0.12
  arr_prod_peso := ARRAY[0.10, 0.12, 0.10, 0.08, 0.18, 0.20, 0.10, 0.12];

  d := DATE '2026-05-09';
  WHILE d <= DATE '2026-05-15' LOOP
    dow := EXTRACT(DOW FROM d);

    -- Pular domingos (2026-05-10 = domingo)
    IF dow = 0 THEN
      d := d + 1;
      CONTINUE;
    END IF;

    IF dow IN (5, 6) THEN
      n_ped := 30 + floor(random() * 6)::int;
    ELSE
      n_ped := 22 + floor(random() * 6)::int;
    END IF;

    FOR i IN 1..n_ped LOOP
      -- Canal distribution: 55% ifood, 25% balcao, 20% whatsapp
      rand_val := random();
      IF rand_val < 0.55 THEN
        canal_val := 'ifood';
      ELSIF rand_val < 0.80 THEN
        canal_val := 'balcao';
      ELSE
        canal_val := 'whatsapp';
      END IF;

      -- Hora: 35% almoço (11-13h), 65% jantar (18-21h)
      IF random() < 0.35 THEN
        hora_h := 11 + floor(random() * 2)::int;
      ELSE
        hora_h := 18 + floor(random() * 3)::int;
      END IF;
      hora_m := floor(random() * 60)::int;

      hora_val := (d::text || ' ' || lpad(hora_h::text, 2, '0') || ':' || lpad(hora_m::text, 2, '0') || ':00-03')::timestamptz;

      -- Create the order (we'll update total after items)
      INSERT INTO pedidos (numero_pedido, data_pedido, canal, subtotal, taxa_entrega, taxa_plataforma, desconto, total, status)
      VALUES (
        'GRI-' || to_char(d, 'MMDD') || '-' || lpad(i::text, 3, '0'),
        hora_val,
        canal_val,
        0, -- placeholder
        CASE WHEN canal_val = 'ifood' THEN round(3 + random() * 4, 2) ELSE 0 END,
        CASE WHEN canal_val = 'ifood' THEN 0 ELSE 0 END, -- taxa cobrada no fechamento
        0,
        0, -- placeholder
        CASE WHEN d < DATE '2026-05-15' THEN 'concluido' ELSE 'concluido' END
      )
      RETURNING id INTO ped_id;

      -- Number of line items per order: 1-3 (weighted toward 1-2)
      rand_val := random();
      IF rand_val < 0.40 THEN
        n_itens := 1;
      ELSIF rand_val < 0.80 THEN
        n_itens := 2;
      ELSE
        n_itens := 3;
      END IF;

      sub := 0;

      FOR j IN 1..n_itens LOOP
        -- Weighted random product selection
        item_rand := random();

        -- Cumulative: 0.10, 0.22, 0.32, 0.40, 0.58, 0.78, 0.88, 1.00
        IF item_rand < 0.10 THEN
          prod_id := arr_prod_id[1]; prod_preco := arr_prod_preco[1]; -- Batata Frita
        ELSIF item_rand < 0.22 THEN
          prod_id := arr_prod_id[2]; prod_preco := arr_prod_preco[2]; -- Combo Explosao
        ELSIF item_rand < 0.32 THEN
          prod_id := arr_prod_id[3]; prod_preco := arr_prod_preco[3]; -- Combo Simples
        ELSIF item_rand < 0.40 THEN
          prod_id := arr_prod_id[4]; prod_preco := arr_prod_preco[4]; -- Refrigerante Lata
        ELSIF item_rand < 0.58 THEN
          prod_id := arr_prod_id[5]; prod_preco := arr_prod_preco[5]; -- Smash Bacon
        ELSIF item_rand < 0.78 THEN
          prod_id := arr_prod_id[6]; prod_preco := arr_prod_preco[6]; -- Smash Duplo
        ELSIF item_rand < 0.88 THEN
          prod_id := arr_prod_id[7]; prod_preco := arr_prod_preco[7]; -- Smash Especial
        ELSE
          prod_id := arr_prod_id[8]; prod_preco := arr_prod_preco[8]; -- Smash Simples
        END IF;

        qtd := 1;
        -- Small chance of quantity 2 for burgers/batata
        IF random() < 0.10 THEN
          qtd := 2;
        END IF;

        INSERT INTO itens_pedido (pedido_id, produto_id, quantidade, preco_unitario, preco_total)
        VALUES (ped_id, prod_id, qtd, prod_preco, prod_preco * qtd);

        sub := sub + (prod_preco * qtd);
      END LOOP;

      -- Update order totals
      UPDATE pedidos
      SET subtotal = sub,
          total = sub + taxa_entrega
      WHERE id = ped_id;

    END LOOP;

    d := d + 1;
  END LOOP;
END $$;

-- ============================================================
-- 7. Reabilitar triggers
-- ============================================================
ALTER TABLE itens_pedido ENABLE TRIGGER trg_baixar_estoque;
ALTER TABLE itens_nota_fiscal ENABLE TRIGGER trg_entrada_nota_fiscal;

-- ============================================================
-- FIM DO SEED
-- ============================================================
