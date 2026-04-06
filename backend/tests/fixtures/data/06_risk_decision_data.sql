-- 决策风险域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO credit_line (id, entity_id, bank_code, credit_limit, used_amount, expire_date) VALUES
('623dac87-4a5e-4568-b6d9-66213b0aef90', 'test_sub_east_b', 'ABC', '260780627.55', '137167291.83', '2025-10-20'),
('242cccf9-dfb6-4ee5-9dce-55465cce98f1', 'test_sub_east_b', 'CMB', '863517145.16', '271439024.50', '2025-10-07'),
('ac30351e-dc5a-489a-ba2d-f10de4703baa', 'test_sub_east_a', 'CITIC', '801348987.40', '345449860.74', '2026-03-27'),
('3eebda0c-773f-407e-8f5b-45b4899620e0', 'test_sub_east_b', 'CEB', '345646262.12', '123065680.52', '2026-01-12'),
('075143c4-d4c2-40ef-ac1d-bb8e03e628f3', 'test_sub_north_a', 'CITIC', '274053488.84', '89008038.14', '2025-03-22'),
('13aacd97-b48b-40cf-8256-34353b806158', 'test_sub_east_b', 'SPDB', '606428765.84', '331536051.93', '2025-10-28'),
('0ddd50fe-3f37-45ed-adbe-95bc1f86a478', 'test_sub_east_b', 'BOCOM', '111571928.70', '44447575.50', '2025-11-10'),
('0e3a103c-6b59-4a96-8fe0-3522fcfc24c7', 'test_sub_east_b', 'CEB', '606595411.45', '463388796.20', '2025-12-26'),
('2f4d0c42-554b-414b-9b95-4eb18afff66a', 'test_sub_east_b', 'CMB', '51931611.22', '43129492.70', '2026-09-22'),
('c4a316ff-a4ca-438c-ae67-ddf368e0ac9a', 'test_sub_east_b', 'ICBC', '281809806.47', '278485142.63', '2025-03-18');

INSERT INTO guarantee (id, guarantor_id, beneficiary_id, amount, guarantee_type, start_date, end_date) VALUES
('4e8c198a-b1ca-49db-b200-987d38ae2a94', 'test_sub_north_a', 'test_sub_east_b', '401542507.90', 'joint', '2024-04-03', '2026-03-09'),
('20c82c38-0da6-4394-b4cb-9884e665744e', 'test_sub_east_a', 'test_sub_east_b', '38280514.72', 'pledge', '2024-01-09', '2024-11-13'),
('7177c527-f0fe-4143-b718-b7f33b492ecc', 'test_sub_east_b', 'test_sub_east_a', '341135718.17', 'pledge', '2024-06-03', '2025-05-06'),
('7de8abec-511a-47da-8638-80b196ff870a', 'test_sub_east_b', 'test_sub_east_a', '267082641.36', 'mortgage', '2024-05-26', '2025-04-11'),
('c61e51ca-6efc-4c83-8286-3a31e1843af6', 'test_sub_north_a', 'test_sub_east_b', '17827103.73', 'joint', '2024-03-04', '2024-12-25');

INSERT INTO related_transaction (id, entity_a_id, entity_b_id, amount, transaction_type, transaction_date) VALUES
('932ec08d-da13-4a45-be86-a0df3836b6fc', 'test_sub_north_a', 'test_sub_east_b', '91362896.33', 'purchase', '2024-05-14'),
('7aaa87be-357a-46dc-b211-c6db21953426', 'test_sub_north_a', 'test_sub_east_b', '21535585.50', 'lease', '2024-05-26'),
('e91445ca-0b92-411d-bd32-04c529f687e6', 'test_sub_east_b', 'test_sub_east_a', '12351478.45', 'purchase', '2024-08-19'),
('85fc906b-fe37-4cf3-b7f4-fe0460943f94', 'test_sub_north_a', 'test_sub_east_b', '99726514.16', 'service', '2024-06-12'),
('1394c447-e5c8-47d7-8129-61bc17236226', 'test_sub_east_b', 'test_sub_east_a', '55044715.03', 'loan', '2024-06-02'),
('2ad2b39b-9fd7-49dc-af0f-e24f16dbf886', 'test_sub_north_a', 'test_sub_east_a', '79390268.75', 'lease', '2024-04-24'),
('82e86031-aa5a-4059-b845-83a3a8fba486', 'test_sub_east_a', 'test_sub_north_a', '23749944.81', 'guarantee', '2024-01-14'),
('9c0bcf32-696b-4b60-9c36-a324f2a18036', 'test_sub_north_a', 'test_sub_east_b', '46793843.35', 'lease', '2024-03-07'),
('fb59301e-9b04-4e64-855b-42a6c91c5297', 'test_sub_east_a', 'test_sub_north_a', '30998142.68', 'service', '2024-09-02'),
('6196bc48-09aa-4cdc-bdf8-109147f4f4b6', 'test_sub_east_b', 'test_sub_north_a', '82351606.01', 'purchase', '2024-03-05');

INSERT INTO derivative (id, entity_id, instrument_type, notional_amount, market_value, maturity_date) VALUES
('1cfb21f4-a41b-46a5-8643-3a6b915ddb39', 'test_sub_east_b', 'fx_option', '324745908.80', '323121351.01', '2025-09-20'),
('d6a2dcd7-dab2-46d1-9c78-3fe47ba350d6', 'test_sub_north_a', 'fx_forward', '323499025.39', '313210563.85', '2027-06-06'),
('34ab134c-f7f3-4f97-acae-a345f1a0010f', 'test_sub_north_a', 'interest_rate_swap', '456249012.76', '435964767.93', '2027-11-28'),
('656d6b88-60a2-421a-802c-19d1e050aa54', 'test_sub_east_a', 'fx_forward', '159021025.98', '129792435.99', '2026-12-10'),
('9f8e928c-b8e7-4ed2-a384-5e32280b6966', 'test_sub_north_a', 'fx_option', '448513699.24', '300139420.79', '2026-02-07');

