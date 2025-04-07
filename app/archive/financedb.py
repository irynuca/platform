import financedatabase as fd

#am verificat daca exista romania si companii din ro, dar nu.

# Initialize the Equities database
equities = fd.Equities()

# Obtain all countries from the database
equities_countries = equities.options('country')

# Obtain all sectors from the database
equities_sectors = equities.options('sector')

# Obtain all industry groups from the database
equities_industry_groups = equities.options('industry_group')

# Obtain all industries from a country from the database
equities_germany_industries = equities.options('industry', country='Romania')

# Obtain a selection from the database
equities_romania = equities.select(country="Romania")

# Obtain a detailed selection from the database
equities_usa_consumer_electronics = equities.select(country="Romania", industry="Banks")

print(equities_romania)