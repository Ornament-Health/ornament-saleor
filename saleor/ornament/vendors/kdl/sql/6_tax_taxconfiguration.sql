update
    tax_taxconfiguration
set
    charge_taxes = false,
    tax_calculation_strategy = null,
    display_gross_prices = true
where
    id = 1;

insert into
    tax_taxconfiguration (
        private_metadata,
        metadata,
        charge_taxes,
        tax_calculation_strategy,
        display_gross_prices,
        prices_entered_with_tax,
        channel_id
    )
values
    ('{}', '{}', false, NULL, true, false, 2),
    ('{}', '{}', false, NULL, true, false, 3),
    ('{}', '{}', false, NULL, true, false, 4),
    ('{}', '{}', false, NULL, true, false, 5),
    ('{}', '{}', false, NULL, true, false, 6),
    ('{}', '{}', false, NULL, true, false, 7),
    ('{}', '{}', false, NULL, true, false, 8),
    ('{}', '{}', false, NULL, true, false, 9),
    ('{}', '{}', false, NULL, true, false, 10),
    ('{}', '{}', false, NULL, true, false, 11),
    ('{}', '{}', false, NULL, true, false, 12),
    ('{}', '{}', false, NULL, true, false, 13),
    ('{}', '{}', false, NULL, true, false, 14),
    ('{}', '{}', false, NULL, true, false, 15),
    ('{}', '{}', false, NULL, true, false, 16),
    ('{}', '{}', false, NULL, true, false, 17),
    ('{}', '{}', false, NULL, true, false, 18),
    ('{}', '{}', false, NULL, true, false, 19),
    ('{}', '{}', false, NULL, true, false, 20),
    ('{}', '{}', false, NULL, true, false, 21);