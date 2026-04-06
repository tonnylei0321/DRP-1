-- 决策风险域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO credit_line (id, entity_id, bank_code, credit_limit, used_amount, expire_date) VALUES
('471cbd82-5add-450f-b018-378219776352', 'test_sub_east_b', 'ABC', '260780627.55', '137167291.83', '2025-10-20'),
('3ddd94c1-a540-453b-a7e4-c55856cc200c', 'test_sub_east_b', 'CMB', '863517145.16', '271439024.50', '2025-10-07'),
('f919c662-00eb-4ec9-9fbd-1e7169926ad8', 'test_sub_east_a', 'CITIC', '801348987.40', '345449860.74', '2026-03-27'),
('8bb47733-ff2d-4ada-9081-2745dc136a6c', 'test_sub_east_b', 'CEB', '345646262.12', '123065680.52', '2026-01-12'),
('2da97380-c884-4f90-b85e-2b7a6861e377', 'test_sub_north_a', 'CITIC', '274053488.84', '89008038.14', '2025-03-22'),
('9e6029fa-cbc1-4c6e-9bbe-4d516e2c3c11', 'test_sub_east_b', 'SPDB', '606428765.84', '331536051.93', '2025-10-28'),
('73dbba57-bbe2-435b-a556-1934ae5769aa', 'test_sub_east_b', 'BOCOM', '111571928.70', '44447575.50', '2025-11-10'),
('136ebf8e-5886-417a-b387-b72206add1d6', 'test_sub_east_b', 'CEB', '606595411.45', '463388796.20', '2025-12-26'),
('38eb5645-caa4-449a-9c5b-9af3f0dbce4d', 'test_sub_east_b', 'CMB', '51931611.22', '43129492.70', '2026-09-22'),
('7cebf390-f43a-4141-a8b7-d9a788fc96cf', 'test_sub_east_b', 'ICBC', '281809806.47', '278485142.63', '2025-03-18');

INSERT INTO guarantee (id, guarantor_id, beneficiary_id, amount, guarantee_type, start_date, end_date) VALUES
('50423251-da2e-46e2-84c4-64fb216ee19e', 'test_sub_north_a', 'test_sub_east_b', '401542507.90', 'joint', '2024-04-03', '2026-03-09'),
('6f089ccf-e392-4698-96a9-adfc4e9771d1', 'test_sub_east_a', 'test_sub_east_b', '38280514.72', 'pledge', '2024-01-09', '2024-11-13'),
('df657def-cb57-4555-ab9d-c88998040955', 'test_sub_east_b', 'test_sub_east_a', '341135718.17', 'pledge', '2024-06-03', '2025-05-06'),
('2273878b-3b99-488d-a734-f262913e659f', 'test_sub_east_b', 'test_sub_east_a', '267082641.36', 'mortgage', '2024-05-26', '2025-04-11'),
('13378b59-4cf3-454d-8c7b-4f2e2617eca3', 'test_sub_north_a', 'test_sub_east_b', '17827103.73', 'joint', '2024-03-04', '2024-12-25');

INSERT INTO related_transaction (id, entity_a_id, entity_b_id, amount, transaction_type, transaction_date) VALUES
('5c892896-d580-4b1d-b965-5b8d79457be0', 'test_sub_north_a', 'test_sub_east_b', '91362896.33', 'purchase', '2024-05-14'),
('7da69a96-64dd-42b8-a629-b0578626d08e', 'test_sub_north_a', 'test_sub_east_b', '21535585.50', 'lease', '2024-05-26'),
('12f21293-c93e-48e4-bbdb-a10df91cf92e', 'test_sub_east_b', 'test_sub_east_a', '12351478.45', 'purchase', '2024-08-19'),
('352aa557-8f7b-4222-989e-f311e9cba2f3', 'test_sub_north_a', 'test_sub_east_b', '99726514.16', 'service', '2024-06-12'),
('d8d9f89d-1254-4adb-9a5b-3012a10aa19c', 'test_sub_east_b', 'test_sub_east_a', '55044715.03', 'loan', '2024-06-02'),
('e1434533-be54-46e5-be4d-2d880bce88a8', 'test_sub_north_a', 'test_sub_east_a', '79390268.75', 'lease', '2024-04-24'),
('7bd54120-97bd-4c22-9e1b-5c34a3bb1109', 'test_sub_east_a', 'test_sub_north_a', '23749944.81', 'guarantee', '2024-01-14'),
('014f0278-fc73-4afe-a6bd-a291a40189f7', 'test_sub_north_a', 'test_sub_east_b', '46793843.35', 'lease', '2024-03-07'),
('0faee8bf-0248-42a0-bdba-26d8fdefad0a', 'test_sub_east_a', 'test_sub_north_a', '30998142.68', 'service', '2024-09-02'),
('397fe753-e27a-4fb0-a1ff-8b571136d6a0', 'test_sub_east_b', 'test_sub_north_a', '82351606.01', 'purchase', '2024-03-05');

INSERT INTO derivative (id, entity_id, instrument_type, notional_amount, market_value, maturity_date) VALUES
('18bbb970-0a2b-4a5f-8301-e67a7f6c9633', 'test_sub_east_b', 'fx_option', '324745908.80', '323121351.01', '2025-09-20'),
('2202d9d7-1ad2-4fc7-acb4-2a3d398c8abe', 'test_sub_north_a', 'fx_forward', '323499025.39', '313210563.85', '2027-06-06'),
('37246c95-4079-4bb4-87b3-3c37e5ff7f5a', 'test_sub_north_a', 'interest_rate_swap', '456249012.76', '435964767.93', '2027-11-28'),
('cc94c063-5220-40d3-9461-73d25852b72b', 'test_sub_east_a', 'fx_forward', '159021025.98', '129792435.99', '2026-12-10'),
('e7a4ec26-91ba-4663-8bf9-5d1f65fc342a', 'test_sub_north_a', 'fx_option', '448513699.24', '300139420.79', '2026-02-07');

