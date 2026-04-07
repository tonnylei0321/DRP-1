-- 债务融资域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO loan (id, entity_id, bank_code, principal, interest_rate, start_date, end_date, status) VALUES
('e6323be5-e3fe-4a36-bd5c-59c8ed4282b4', 'test_sub_north_a', 'ABC', '408534924.67', '0.0431', '2023-05-31', '2026-03-26', 'active'),
('716d3db5-5bb1-4b37-8d25-a985fb0d4b8e', 'test_sub_east_b', 'SPDB', '187606782.35', '0.0316', '2023-01-28', '2024-09-23', 'active'),
('dacac26b-eb16-426f-b84b-f1d361cec452', 'test_sub_east_b', 'CMB', '465482126.47', '0.0367', '2023-03-25', '2024-10-08', 'active'),
('7d9d9660-bb47-4bf8-b6fd-7b7319cf37f1', 'test_sub_north_a', 'ICBC', '144152819.26', '0.0344', '2023-12-10', '2026-08-26', 'active'),
('61b8f269-818a-4353-a433-c5192388b127', 'test_sub_east_b', 'CEB', '308058780.32', '0.0512', '2023-05-23', '2026-01-04', 'active'),
('add6310e-8383-41a2-8e0a-27c2019397af', 'test_sub_east_a', 'CCB', '274853318.48', '0.0365', '2023-01-20', '2024-04-06', 'active'),
('7f9c179b-2e64-4b06-a378-8dcdd1d3ba17', 'test_sub_north_a', 'BOCOM', '119582473.09', '0.0333', '2024-06-24', '2026-02-27', 'active'),
('619d9247-d08d-491c-8f91-6d04f98e9d00', 'test_sub_east_a', 'CEB', '32340768.35', '0.0426', '2023-02-18', '2024-04-17', 'active'),
('3306d1ad-c6c7-4ab6-af44-fa46e123f4de', 'test_sub_east_b', 'ABC', '359553619.57', '0.0455', '2023-01-17', '2025-04-23', 'active'),
('117482c2-1160-4e08-a9c0-76148d633d76', 'test_sub_east_b', 'CITIC', '94469641.99', '0.0724', '2024-03-15', '2024-09-12', 'active');

INSERT INTO bond (id, entity_id, bond_code, face_value, coupon_rate, maturity_date, status) VALUES
('61e22f73-567f-4e82-b7f0-a7268610587c', 'test_sub_north_a', 'BD189772', '528249712.10', '0.0408', '2027-12-14', 'active'),
('a84b9cbb-3379-4770-a95f-6a8a09cd6bc0', 'test_sub_north_a', 'BD631971', '788548212.49', '0.0452', '2025-02-11', 'active'),
('847bada8-4a92-4a5f-b00b-44f9d29a7d0f', 'test_sub_east_b', 'BD592972', '53099080.92', '0.0416', '2027-02-04', 'active'),
('17acb393-b2fc-4ee3-87e2-09d170f6beff', 'test_sub_east_b', 'BD883618', '26079808.80', '0.0537', '2026-12-08', 'active'),
('0b54afbb-e12e-4873-9d67-19dfea6a0f38', 'test_sub_east_a', 'BD868544', '660533356.01', '0.0331', '2028-04-06', 'active');

INSERT INTO finance_lease (id, entity_id, lessor, lease_amount, monthly_payment, start_date, end_date) VALUES
('8cf9448f-328a-4a53-9a90-5ef47707c9ca', 'test_sub_north_a', '招银租赁', '13645459.22', '649783.77', '2023-12-07', '2025-09-05'),
('5f467a17-44ab-492a-a69f-b7334bfdb019', 'test_sub_east_b', '交银租赁', '95601465.45', '1648301.13', '2023-06-29', '2028-04-30'),
('201be41d-ed51-4ba6-b968-a43d95124b07', 'test_sub_north_a', '交银租赁', '17304604.72', '824028.80', '2023-07-06', '2025-04-07'),
('443774c6-55ec-4eca-96ac-29fc32db7a3e', 'test_sub_east_a', '中银租赁', '13542223.75', '541688.95', '2023-10-28', '2025-12-13'),
('05e0182f-8a2d-428e-bbfd-cbd36ab43906', 'test_sub_east_a', '招银租赁', '105499799.90', '3196963.63', '2023-11-20', '2026-08-16');

