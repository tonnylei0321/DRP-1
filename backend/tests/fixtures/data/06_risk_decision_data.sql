-- 决策风险域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO credit_line (id, entity_id, bank_code, credit_limit, used_amount, expire_date) VALUES
('8fed502e-3f93-4574-8bee-979a24ce4ed6', 'test_sub_east_b', 'ABC', '260780627.55', '137167291.83', '2025-10-20'),
('83d74be6-4fd3-4cde-b980-4a51427bacef', 'test_sub_east_b', 'CMB', '863517145.16', '271439024.50', '2025-10-07'),
('93867a51-e165-4021-b3f6-a83adbf417e6', 'test_sub_east_a', 'CITIC', '801348987.40', '345449860.74', '2026-03-27'),
('e08c470c-7c7f-4d21-95d3-383484d816b7', 'test_sub_east_b', 'CEB', '345646262.12', '123065680.52', '2026-01-12'),
('98db200b-c576-4a57-9f75-966a629445b5', 'test_sub_north_a', 'CITIC', '274053488.84', '89008038.14', '2025-03-22'),
('adefab07-7860-40d5-9b03-4a2f2412492b', 'test_sub_east_b', 'SPDB', '606428765.84', '331536051.93', '2025-10-28'),
('ec98ca57-6209-4edc-9c79-1622849ccfb6', 'test_sub_east_b', 'BOCOM', '111571928.70', '44447575.50', '2025-11-10'),
('8424d1a4-7266-4a09-bcda-6b47f4f145be', 'test_sub_east_b', 'CEB', '606595411.45', '463388796.20', '2025-12-26'),
('4d70e045-4fbd-43f3-9e97-0b021ba38483', 'test_sub_east_b', 'CMB', '51931611.22', '43129492.70', '2026-09-22'),
('968706e9-6b5c-48e3-bee1-aeec0787138f', 'test_sub_east_b', 'ICBC', '281809806.47', '278485142.63', '2025-03-18');

INSERT INTO guarantee (id, guarantor_id, beneficiary_id, amount, guarantee_type, start_date, end_date) VALUES
('ec67a601-6153-4d0c-b9d8-e8076a1244f6', 'test_sub_north_a', 'test_sub_east_b', '401542507.90', 'joint', '2024-04-03', '2026-03-09'),
('8cf83b7a-660e-4cd8-9b45-482c05e8a53f', 'test_sub_east_a', 'test_sub_east_b', '38280514.72', 'pledge', '2024-01-09', '2024-11-13'),
('d6875d1d-c18c-4152-9146-de7009c18628', 'test_sub_east_b', 'test_sub_east_a', '341135718.17', 'pledge', '2024-06-03', '2025-05-06'),
('1561349a-8cab-4b44-ab67-158b05d19fe0', 'test_sub_east_b', 'test_sub_east_a', '267082641.36', 'mortgage', '2024-05-26', '2025-04-11'),
('c77bd1a6-d368-4a31-b6f7-96514f45225e', 'test_sub_north_a', 'test_sub_east_b', '17827103.73', 'joint', '2024-03-04', '2024-12-25');

INSERT INTO related_transaction (id, entity_a_id, entity_b_id, amount, transaction_type, transaction_date) VALUES
('28e03445-76d3-415b-9c31-e2774c8b4b26', 'test_sub_north_a', 'test_sub_east_b', '91362896.33', 'purchase', '2024-05-14'),
('502c7b1a-fdbf-4c85-a999-1b17631b5a59', 'test_sub_north_a', 'test_sub_east_b', '21535585.50', 'lease', '2024-05-26'),
('6f85906c-7587-4e33-991d-e39c54f0da76', 'test_sub_east_b', 'test_sub_east_a', '12351478.45', 'purchase', '2024-08-19'),
('81878f74-53a7-4202-8668-07353165ad2e', 'test_sub_north_a', 'test_sub_east_b', '99726514.16', 'service', '2024-06-12'),
('de358acf-3a12-4efc-8be8-12a0529fd43f', 'test_sub_east_b', 'test_sub_east_a', '55044715.03', 'loan', '2024-06-02'),
('59ddc590-7618-41af-a849-212152fc0e69', 'test_sub_north_a', 'test_sub_east_a', '79390268.75', 'lease', '2024-04-24'),
('0e0a7f44-4c6d-492b-b457-87e3208355df', 'test_sub_east_a', 'test_sub_north_a', '23749944.81', 'guarantee', '2024-01-14'),
('9d3ab5fc-e8f6-4524-9d2e-2dc271cd7760', 'test_sub_north_a', 'test_sub_east_b', '46793843.35', 'lease', '2024-03-07'),
('7e072272-8919-42ec-9559-dd7e394f6bea', 'test_sub_east_a', 'test_sub_north_a', '30998142.68', 'service', '2024-09-02'),
('71e096bd-91f8-457b-9aab-7058050bd287', 'test_sub_east_b', 'test_sub_north_a', '82351606.01', 'purchase', '2024-03-05');

INSERT INTO derivative (id, entity_id, instrument_type, notional_amount, market_value, maturity_date) VALUES
('e183a228-f4af-4e31-818c-3f67da5d96e2', 'test_sub_east_b', 'fx_option', '324745908.80', '323121351.01', '2025-09-20'),
('e0cd8697-3b57-44ff-b50e-f8b16a129dff', 'test_sub_north_a', 'fx_forward', '323499025.39', '313210563.85', '2027-06-06'),
('c23c5e4a-70d4-4cd5-befb-6883553239aa', 'test_sub_north_a', 'interest_rate_swap', '456249012.76', '435964767.93', '2027-11-28'),
('42488c2f-3376-4d98-881e-fced6fbf677a', 'test_sub_east_a', 'fx_forward', '159021025.98', '129792435.99', '2026-12-10'),
('8a934f37-f263-481a-ac17-eac7c508cd9c', 'test_sub_north_a', 'fx_option', '448513699.24', '300139420.79', '2026-02-07');

