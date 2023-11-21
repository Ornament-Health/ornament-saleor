insert into
    attribute_attribute (
        id,
        slug,
        name,
        metadata,
        private_metadata,
        input_type,
        available_in_grid,
        visible_in_storefront,
        filterable_in_dashboard,
        filterable_in_storefront,
        value_required,
        storefront_search_position,
        is_variant_only,
        type
    )
values
    (
        1,
        'color',
        'Color',
        '{}',
        '{}',
        'swatch',
        true,
        true,
        true,
        false,
        true,
        0,
        false,
        'product-type'
    ),
    (
        2,
        'featured',
        'Featured',
        '{}',
        '{}',
        'boolean',
        false,
        true,
        true,
        false,
        false,
        0,
        false,
        'product-type'
    ),
    (
        3,
        'featured-collection',
        'Featured collection',
        '{}',
        '{}',
        'boolean',
        false,
        true,
        true,
        false,
        false,
        0,
        false,
        'product-type'
    ),
    (
        4,
        'icon',
        'Icon',
        '{}',
        '{}',
        'swatch',
        true,
        true,
        true,
        false,
        false,
        0,
        false,
        'product-type'
    ),
    (
        5000,
        'kdl-biomaterials',
        'KDL Biomaterials',
        '{}',
        '{}',
        'plain-text',
        false,
        true,
        false,
        false,
        false,
        0,
        false,
        'product-type'
    ),
    (
        10000,
        'kdl-preparation',
        'KDL Preparation',
        '{}',
        '{}',
        'rich-text',
        false,
        true,
        false,
        false,
        false,
        0,
        false,
        'product-type'
    ),
    (
        15000,
        'kdl-max_duration',
        'KDL Max Duration',
        '{}',
        '{}',
        'numeric',
        false,
        true,
        false,
        false,
        false,
        0,
        false,
        'product-type'
    ),
    (
        20000,
        'kdl-duration_unit',
        'KDL Duration Unit',
        '{}',
        '{}',
        'numeric',
        false,
        true,
        false,
        false,
        false,
        0,
        false,
        'product-type'
    ),
    (
        25000,
        'sex',
        'Sex',
        '{}',
        '{}',
        'dropdown',
        false,
        true,
        false,
        false,
        false,
        0,
        false,
        'product-type'
    ),
    (
        30000,
        'age-from',
        'Age From',
        '{}',
        '{}',
        'numeric',
        false,
        true,
        false,
        false,
        false,
        0,
        false,
        'product-type'
    ),
    (
        35000,
        'age-to',
        'Age To',
        '{}',
        '{}',
        'numeric',
        false,
        true,
        false,
        false,
        false,
        0,
        false,
        'product-type'
    ),
    (
        40000,
        'biomarkers',
        'Biomarkers',
        '{}',
        '{}',
        'multiselect',
        true,
        true,
        true,
        true,
        false,
        0,
        false,
        'product-type'
    ),
    (
        50000,
        'medical_exams',
        'Medical Exams',
        '{}',
        '{}',
        'multiselect',
        true,
        true,
        true,
        true,
        false,
        0,
        false,
        'product-type'
    );