insert into
    discount_voucher (
        id,
        "type",
        "name",
        code,
        usage_limit,
        used,
        start_date,
        end_date,
        discount_value_type,
        apply_once_per_order,
        countries,
        min_checkout_items_quantity,
        apply_once_per_customer,
        only_for_staff,
        metadata,
        private_metadata,
        "scope"
    )
values
    (
        1,
        'entire_order',
        null,
        'SUBSCRIPTION-MONTHLY',
        null,
        0,
        '2023-10-17 19:02:44.550',
        null,
        'percentage',
        false,
        '',
        0,
        false,
        false,
        '{}' :: jsonb,
        '{}' :: jsonb,
        'retail'
    ),
    (
        2,
        'entire_order',
        null,
        'SUBSCRIPTION-ANNUAL',
        null,
        0,
        '2023-10-17 19:03:17.421',
        null,
        'percentage',
        false,
        '',
        0,
        false,
        false,
        '{}' :: jsonb,
        '{}' :: jsonb,
        'retail'
    );

insert into
    discount_voucherchannellisting (
        id,
        discount_value,
        currency,
        min_spent_amount,
        channel_id,
        voucher_id
    )
values
    (44, 10.000, 'RUB', NULL, 12, 1),
    (45, 10.000, 'RUB', NULL, 10, 1),
    (46, 10.000, 'RUB', NULL, 2, 1),
    (47, 10.000, 'RUB', NULL, 15, 1),
    (48, 10.000, 'RUB', NULL, 19, 1),
    (49, 10.000, 'RUB', NULL, 20, 1),
    (50, 10.000, 'RUB', NULL, 9, 1),
    (51, 10.000, 'RUB', NULL, 5, 1),
    (52, 10.000, 'RUB', NULL, 3, 1),
    (53, 10.000, 'RUB', NULL, 1, 1),
    (54, 10.000, 'RUB', NULL, 17, 1),
    (55, 10.000, 'RUB', NULL, 18, 1),
    (56, 10.000, 'RUB', NULL, 4, 1),
    (57, 10.000, 'RUB', NULL, 11, 1),
    (58, 10.000, 'RUB', NULL, 21, 1),
    (59, 10.000, 'RUB', NULL, 13, 1),
    (60, 10.000, 'RUB', NULL, 14, 1),
    (61, 10.000, 'RUB', NULL, 6, 1),
    (62, 10.000, 'RUB', NULL, 8, 1),
    (63, 10.000, 'RUB', NULL, 7, 1),
    (64, 10.000, 'RUB', NULL, 16, 1),
    (65, 20.000, 'RUB', NULL, 12, 2),
    (66, 20.000, 'RUB', NULL, 10, 2),
    (67, 20.000, 'RUB', NULL, 2, 2),
    (68, 20.000, 'RUB', NULL, 15, 2),
    (69, 20.000, 'RUB', NULL, 19, 2),
    (70, 20.000, 'RUB', NULL, 20, 2),
    (71, 20.000, 'RUB', NULL, 9, 2),
    (72, 20.000, 'RUB', NULL, 5, 2),
    (73, 20.000, 'RUB', NULL, 3, 2),
    (74, 20.000, 'RUB', NULL, 1, 2),
    (75, 20.000, 'RUB', NULL, 17, 2),
    (76, 20.000, 'RUB', NULL, 18, 2),
    (77, 20.000, 'RUB', NULL, 4, 2),
    (78, 20.000, 'RUB', NULL, 11, 2),
    (79, 20.000, 'RUB', NULL, 21, 2),
    (80, 20.000, 'RUB', NULL, 13, 2),
    (81, 20.000, 'RUB', NULL, 14, 2),
    (82, 20.000, 'RUB', NULL, 6, 2),
    (83, 20.000, 'RUB', NULL, 8, 2),
    (84, 20.000, 'RUB', NULL, 7, 2),
    (85, 20.000, 'RUB', NULL, 16, 2);