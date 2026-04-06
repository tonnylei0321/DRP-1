-- 债务融资域 测试数据
-- 自动生成，请勿手动修改

INSERT INTO loan (id, entity_id, bank_code, principal, interest_rate, start_date, end_date, status) VALUES
('9f964448-7109-4717-b54d-6c883e597ee5', 'test_sub_north_a', 'ABC', '408534924.67', '0.0431', '2023-05-31', '2026-03-26', 'active'),
('aadd633e-1f98-45be-9c19-d60c61345697', 'test_sub_east_b', 'SPDB', '187606782.35', '0.0316', '2023-01-28', '2024-09-23', 'active'),
('79cc152c-6e2a-471c-9e05-4dc994d03255', 'test_sub_east_b', 'CMB', '465482126.47', '0.0367', '2023-03-25', '2024-10-08', 'active'),
('ae2c91c9-637c-4194-a93c-f7fd390070d5', 'test_sub_north_a', 'ICBC', '144152819.26', '0.0344', '2023-12-10', '2026-08-26', 'active'),
('746b96c6-715b-44bf-9569-c8f280b40eca', 'test_sub_east_b', 'CEB', '308058780.32', '0.0512', '2023-05-23', '2026-01-04', 'active'),
('06e89e46-da5e-407d-a5c4-f83e2ad7e835', 'test_sub_east_a', 'CCB', '274853318.48', '0.0365', '2023-01-20', '2024-04-06', 'active'),
('511dc81d-f505-4378-8d47-19ab24881964', 'test_sub_north_a', 'BOCOM', '119582473.09', '0.0333', '2024-06-24', '2026-02-27', 'active'),
('7846d896-052a-4336-9cc2-e5772d999282', 'test_sub_east_a', 'CEB', '32340768.35', '0.0426', '2023-02-18', '2024-04-17', 'active'),
('276bbd1b-e7e6-4baf-ad58-46accbdfb3ab', 'test_sub_east_b', 'ABC', '359553619.57', '0.0455', '2023-01-17', '2025-04-23', 'active'),
('53ff9b4a-26f9-48ae-aca1-008b95a641e1', 'test_sub_east_b', 'CITIC', '94469641.99', '0.0724', '2024-03-15', '2024-09-12', 'active');

INSERT INTO bond (id, entity_id, bond_code, face_value, coupon_rate, maturity_date, status) VALUES
('c14a9ce6-254e-47bc-a49f-50d9abb9fc0f', 'test_sub_north_a', 'BD189772', '528249712.10', '0.0408', '2027-12-14', 'active'),
('5a212d2f-78f3-4341-88ef-84d877ed7a7c', 'test_sub_north_a', 'BD631971', '788548212.49', '0.0452', '2025-02-11', 'active'),
('f8ac3f09-7aca-4808-8dd4-1c2bf4ae97f1', 'test_sub_east_b', 'BD592972', '53099080.92', '0.0416', '2027-02-04', 'active'),
('deac6065-b7ef-4147-ac71-231eb303afbe', 'test_sub_east_b', 'BD883618', '26079808.80', '0.0537', '2026-12-08', 'active'),
('92b11531-b134-42bb-890b-d7e1c4751a98', 'test_sub_east_a', 'BD868544', '660533356.01', '0.0331', '2028-04-06', 'active');

INSERT INTO finance_lease (id, entity_id, lessor, lease_amount, monthly_payment, start_date, end_date) VALUES
('08b0f3b7-bf30-4690-9c45-53b2fd987e8c', 'test_sub_north_a', '招银租赁', '13645459.22', '649783.77', '2023-12-07', '2025-09-05'),
('cdb7aa94-0005-4a57-a139-363fe9383a18', 'test_sub_east_b', '交银租赁', '95601465.45', '1648301.13', '2023-06-29', '2028-04-30'),
('b0517c2f-7d60-41cc-80d8-1ceb6b37670a', 'test_sub_north_a', '交银租赁', '17304604.72', '824028.80', '2023-07-06', '2025-04-07'),
('1f4d442a-2ff1-4622-8112-ae54b700179d', 'test_sub_east_a', '中银租赁', '13542223.75', '541688.95', '2023-10-28', '2025-12-13'),
('a0d2c09e-c9f3-46dc-a2b8-2a28b1432625', 'test_sub_east_a', '招银租赁', '105499799.90', '3196963.63', '2023-11-20', '2026-08-16');

