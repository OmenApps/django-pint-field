# Cheatsheet

All of the examples below use `device = ExperimentalDevice.objects.first()` from `example_project/laboratory/models.py` as the base object. The `ExperimentalDevice` model has a `portal_diameter` field that is a `DecimalPintField` with a default unit of `meter` and unit choices of `meter`, `centimeter`, and `foot`.

## Access and Conversion Examples

### Basic Field Access

| Description                                     | Code                                                             | Output                                               |
|-------------------------------------------------|------------------------------------------------------------------|------------------------------------------------------|
| Field type                                      | ```type(device.portal_diameter)```                             | ```<class 'django_pint_field.helpers.PintFieldProxy'>``` |
| Direct string output                            | ```device.portal_diameter```                                   | ```28.7882182843549 meter```                       |
| Magnitude                                       | ```device.portal_diameter.magnitude```                         | ```28.7882182843549```                             |
| Units                                           | ```device.portal_diameter.units```                             | ```meter```                                        |
| Quantity type                                   | ```type(device.portal_diameter.quantity)```                    | ```<class 'pint.Quantity'>```                      |
| Quantity value                                  | ```device.portal_diameter.quantity```                          | ```28.7882182843549 meter```                       |
| Quantity magnitude                              | ```device.portal_diameter.quantity.magnitude```                | ```28.7882182843549```                             |
| Quantity units                                  | ```device.portal_diameter.quantity.units```                    | ```meter```                                        |
| get_FOO_display() method                        | ```device.get_portal_diameter_display()```                     | ```28.7882182843549 meter```                       |
| get_FOO_display() with digits                   | ```device.get_portal_diameter_display(digits=3)```             | ```28.788 meter```                                 |
| get_FOO_display() with format_string            | ```device.get_portal_diameter_display(format_string='~P')```   | ```28.7882182843549 m```                           |
| get_FOO_display() with digits and format_string | ```device.get_portal_diameter_display(digits=3, format_string='~P')``` | ```28.788 m```                           |

### Unit Conversions

| Description                       | Code                                               | Output                         |
|-----------------------------------|----------------------------------------------------|--------------------------------|
| Convert to kilometers (proxy)     | ```device.portal_diameter.kilometer```           | ```0.0287882182843549 kilometer``` |
| Convert to centimeters (proxy)    | ```device.portal_diameter.centimeter```          | ```2878.82182843549 centimeter```  |
| Convert to millimeters (proxy)    | ```device.portal_diameter.millimeter```          | ```28788.2182843549 millimeter```  |
| Convert to kilometers (quantity)  | ```device.portal_diameter.quantity.to('kilometer')``` | ```0.0287882182843549 kilometer``` |
| Convert to centimeters (quantity) | ```device.portal_diameter.quantity.to('centimeter')``` | ```2878.82182843549 centimeter``` |
| Convert to millimeters (quantity) | ```device.portal_diameter.quantity.to('millimeter')``` | ```28788.2182843549 millimeter``` |

### Decimal Formatting

| Description                         | Code                                   | Output               |
|-------------------------------------|----------------------------------------|----------------------|
| Format with 2 decimal places        | ```device.portal_diameter.digits__2```     | ```28.79 meter```        |
| Format with 3 decimal places        | ```device.portal_diameter.digits__3```     | ```28.788 meter```       |
| Format with 4 decimal places        | ```device.portal_diameter.digits__4```     | ```28.7882 meter```      |
| Convert to km with 3 decimal places | ```device.portal_diameter.kilometer__3```  | ```0.029 kilometer```    |
| Convert to cm with 2 decimal places | ```device.portal_diameter.centimeter__2``` | ```2878.82 centimeter``` |
| Convert to mm with 1 decimal place  | ```device.portal_diameter.millimeter__1``` | ```28788.2 millimeter``` |

### Aggregations

| Description                                   | Code                                                                                                                                | Output                                        |
|-----------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| count                                         | ```ExperimentalDevice.objects.aggregate(count=PintCount('portal_diameter'))['count']```                                           | ```334```                    |
| avg_diameter base value                       | ```ExperimentalDevice.objects.aggregate(avg_diameter=PintAvg('portal_diameter'))['avg_diameter']```                               | ```23.79052932242018032 meter```            |
| avg_diameter raw Quantity                     | ```ExperimentalDevice.objects.aggregate(avg_diameter=PintAvg('portal_diameter'))['avg_diameter'].quantity```                      | ```23.79052932242018032 meter```            |
| avg_diameter raw Quantity magnitude           | ```ExperimentalDevice.objects.aggregate(avg_diameter=PintAvg('portal_diameter'))['avg_diameter'].quantity.magnitude```            | ```23.79052932242018032```                  |
| avg_diameter raw Quantity converted to km     | ```ExperimentalDevice.objects.aggregate(avg_diameter=PintAvg('portal_diameter'))['avg_diameter'].quantity.to('kilometer')```      | ```0.02379052932242018032 kilometer```      |
| avg_diameter in centimeters                   | ```ExperimentalDevice.objects.aggregate(avg_diameter=PintAvg('portal_diameter'))['avg_diameter'].centimeter```                    | ```2379.052932242018032 centimeter```       |
| avg_diameter formatted (2 places)             | ```ExperimentalDevice.objects.aggregate(avg_diameter=PintAvg('portal_diameter'))['avg_diameter'].digits__2```                     | ```23.79 meter```                           |
| max_diameter base value                       | ```ExperimentalDevice.objects.aggregate(max_diameter=PintMax('portal_diameter'))['max_diameter']```                               | ```49.92358960647989 meter```               |
| max_diameter raw Quantity                     | ```ExperimentalDevice.objects.aggregate(max_diameter=PintMax('portal_diameter'))['max_diameter'].quantity```                      | ```49.92358960647989 meter```               |
| max_diameter raw Quantity magnitude           | ```ExperimentalDevice.objects.aggregate(max_diameter=PintMax('portal_diameter'))['max_diameter'].quantity.magnitude```            | ```49.92358960647989```                     |
| max_diameter raw Quantity converted to km     | ```ExperimentalDevice.objects.aggregate(max_diameter=PintMax('portal_diameter'))['max_diameter'].quantity.to('kilometer')```      | ```0.04992358960647989 kilometer```         |
| max_diameter in centimeters                   | ```ExperimentalDevice.objects.aggregate(max_diameter=PintMax('portal_diameter'))['max_diameter'].centimeter```                    | ```4992.358960647989 centimeter```          |
| max_diameter formatted (2 places)             | ```ExperimentalDevice.objects.aggregate(max_diameter=PintMax('portal_diameter'))['max_diameter'].digits__2```                     | ```49.92 meter```                           |
| std_dev_diameter base value                   | ```ExperimentalDevice.objects.aggregate(std_dev_diameter=PintStdDev('portal_diameter'))['std_dev_diameter']```                    | ```15.0849111373296899130475104660377653 meter``` |
| std_dev_diameter raw Quantity                 | ```ExperimentalDevice.objects.aggregate(std_dev_diameter=PintStdDev('portal_diameter'))['std_dev_diameter'].quantity```           | ```15.0849111373296899130475104660377653 meter``` |
| std_dev_diameter raw Quantity magnitude       | ```ExperimentalDevice.objects.aggregate(std_dev_diameter=PintStdDev('portal_diameter'))['std_dev_diameter'].quantity.magnitude``` | ```15.0849111373296899130475104660377653``` |
| std_dev_diameter raw Quantity converted to km | ```ExperimentalDevice.objects.aggregate(std_dev_diameter=PintStdDev('portal_diameter'))['std_dev_diameter'].quantity.to('kilometer')``` | ```0.01508491113732968991304751047 kilometer``` |
| std_dev_diameter in centimeters               | ```ExperimentalDevice.objects.aggregate(std_dev_diameter=PintStdDev('portal_diameter'))['std_dev_diameter'].centimeter```         | ```1508.491113732968991304751047 centimeter``` |
| std_dev_diameter formatted (2 places)         | ```ExperimentalDevice.objects.aggregate(std_dev_diameter=PintStdDev('portal_diameter'))['std_dev_diameter'].digits__2```          | ```15.08 meter```                           |

### Advanced Features

| Description                    | Code                                         | Output                   |
|--------------------------------|----------------------------------------------|--------------------------|
| Original value                 | ```device.portal_diameter```               | ```28.7882182843549 meter``` |
| To km with 3 decimal places    | ```device.portal_diameter.kilometer__3```  | ```0.029 kilometer```        |
| To cm with 2 decimal places    | ```device.portal_diameter.centimeter__2``` | ```2878.82 centimeter```     |
| Kilometer conversion magnitude | ```device.portal_diameter.kilometer.magnitude``` | ```0.0287882182843549```     |
| Kilometer conversion units     | ```device.portal_diameter.kilometer.units``` | ```kilometer```              |

### Comparison Operations

| Description             | Code                                                                         | Output                     |
|-------------------------|------------------------------------------------------------------------------|----------------------------|
| First device diameter   | ```devices[0].portal_diameter```                                           | ```28.7882182843549 meter```   |
| Second device diameter  | ```devices[1].portal_diameter```                                           | ```18.152442920347703 meter``` |
| Equal comparison        | ```devices[0].portal_diameter.quantity == devices[1].portal_diameter.quantity``` | ```False```                    |
| Greater than comparison | ```devices[0].portal_diameter.quantity > devices[1].portal_diameter.quantity```  | ```True```                     |
| Less than comparison    | ```devices[0].portal_diameter.quantity < devices[1].portal_diameter.quantity```  | ```False```                    |

### Field Metadata

| Description            | Code                                                                                             | Output                                                                 |
|------------------------|--------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| Default unit           | ```ExperimentalDevice._meta.get_field('portal_diameter').default_unit```                       | ```meter```                                                          |
| Unit choices           | ```ExperimentalDevice._meta.get_field('portal_diameter').unit_choices```                       | ```[('meter', 'meter'), ('centimeter', 'centimeter'), ('foot', 'foot')]``` |
| Display decimal places | ```getattr(ExperimentalDevice._meta.get_field('portal_diameter'), 'display_decimal_places', None)``` | ```None```                                                                 |

## Template Examples

### Basic Field Access

| Description                          | Template Code                                     | Output                   |
|--------------------------------------|---------------------------------------------------|--------------------------|
| Direct output                        | ```{{ device.portal_diameter }}```              | ```28.7882182843549 meter``` |
| Magnitude only                       | ```{{ device.portal_diameter.magnitude }}```    | ```28.7882182843549```       |
| Units only                           | ```{{ device.portal_diameter.units }}```        | ```meter```                  |
| Raw Pint Quantity object             | ```{{ device.portal_diameter.quantity }}```     | ```28.7882182843549 meter``` |
| Raw Pint Quantity object (magnitude) | ```{{ device.portal_diameter.quantity.magnitude }}``` | ```28.7882182843549```       |
| Raw Pint Quantity object (units)     | ```{{ device.portal_diameter.quantity.units }}``` | ```meter```                  |

### Decimal Place Formatting

| Description                      | Template Code                                      | Output           |
|----------------------------------|----------------------------------------------------|------------------|
| 0 decimal places                 | ```{{ device.portal_diameter.digits__0 }}```     | ```29 meter```       |
| 2 decimal places                 | ```{{ device.portal_diameter.digits__2 }}```     | ```28.79 meter```    |
| 5 decimal places                 | ```{{ device.portal_diameter.digits__5 }}```     | ```28.78822 meter``` |
| 5 decimal places, magnitude only | ```{{ device.portal_diameter.digits__5.magnitude }}``` | ```28.78822```       |

### Direct Conversions

| Description                                    | Template Code                                 | Output                               |
|------------------------------------------------|-----------------------------------------------|--------------------------------------|
| Direct conversion (meter)                      | ```{{ device.portal_diameter.meter }}```    | ```28.7882182843549 meter```       |
| Direct conversion (centimeter)                 | ```{{ device.portal_diameter.centimeter }}``` | ```2878.82182843549 centimeter```  |
| Direct conversion (foot)                       | ```{{ device.portal_diameter.foot }}```     | ```94.44953505365780839895013119 foot``` |
| Direct conversion (foot) magnitude only        | ```{{ device.portal_diameter.foot.magnitude }}``` | ```94.44953505365780839895013119```      |
| Direct conversion (foot) units only            | ```{{ device.portal_diameter.foot.units }}``` | ```foot```                               |
| Direct conversion (foot) with 0 decimal places | ```{{ device.portal_diameter.foot__0 }}```  | ```94 foot```                            |
| Direct conversion (foot) with 2 decimal places | ```{{ device.portal_diameter.foot__2 }}```  | ```94.45 foot```                         |
| Direct conversion (foot) with 5 decimal places | ```{{ device.portal_diameter.foot__5 }}```  | ```94.44954 foot```                      |

### Template Filters

| Description                           | Template Code                                                                         | Output                               |
|---------------------------------------|---------------------------------------------------------------------------------------|--------------------------------------|
| Magnitude only                        | ```{{ device.portal_diameter|magnitude_only }}```                                   | ```28.7882182843549```             |
| Magnitude only with 2 decimal places  | ```{{ device.portal_diameter.digits__2|magnitude_only }}```                         | ```28.79```                        |
| Units only                            | ```{{ device.portal_diameter|units_only }}```                                       | ```meter```                        |
| Convert to meter                      | ```{{ device.portal_diameter|with_units:"meter" }}```                               | ```28.7882182843549 meter```       |
| Convert to meter with 2 decimals      | ```{{ device.portal_diameter|with_units:"meter"|with_digits:2 }}```                 | ```28.79 meter```                  |
| Convert to meter, magnitude only      | ```{{ device.portal_diameter|with_units:"meter"|magnitude_only }}```                | ```28.7882182843549```             |
| Convert to meter, magnitude only      | ```{{ device.portal_diameter|with_units:"meter"|magnitude_only|floatformat:'2' }}``` | ```28.79```                        |
| Convert to meter, units only          | ```{{ device.portal_diameter|with_units:"meter"|units_only }}```                    | ```meter```                        |
| Convert to centimeter                 | ```{{ device.portal_diameter|with_units:"centimeter" }}```                         | ```2878.82182843549 centimeter```  |
| Convert to centimeter with 2 decimals | ```{{ device.portal_diameter|with_units:"centimeter"|with_digits:2 }}```           | ```2878.82 centimeter```           |
| Convert to centimeter, magnitude only | ```{{ device.portal_diameter|with_units:"centimeter"|magnitude_only }}```          | ```2878.82182843549```             |
| Convert to centimeter, magnitude only | ```{{ device.portal_diameter|with_units:"centimeter"|magnitude_only|floatformat:'2' }}``` | ```2878.82```             |
| Convert to centimeter, units only     | ```{{ device.portal_diameter|with_units:"centimeter"|units_only }}```              | ```centimeter```                   |
| Convert to foot                       | ```{{ device.portal_diameter|with_units:"foot" }}```                               | ```94.44953505365780839895013119 foot``` |
| Convert to foot with 2 decimals       | ```{{ device.portal_diameter|with_units:"foot"|with_digits:2 }}```                 | ```94.45 foot```                   |
| Convert to foot, magnitude only       | ```{{ device.portal_diameter|with_units:"foot"|magnitude_only }}```                | ```94.44953505365780839895013119``` |
| Convert to foot, magnitude only       | ```{{ device.portal_diameter|with_units:"foot"|magnitude_only|floatformat:'2' }}``` | ```94.45```                        |
| Convert to foot, units only           | ```{{ device.portal_diameter|with_units:"foot"|units_only }}```                    | ```foot```                         |

### Format String Examples

| Description                        | Template Code                                                  | Output                   |
|------------------------------------|----------------------------------------------------------------|--------------------------|
| Default format                     | ```{{ device.portal_diameter|pint_str_format:'' }}```        | ```28.7882182843549 meter``` |
| Default format (explicitly stated) | ```{{ device.portal_diameter|pint_str_format:'D' }}```       | ```28.7882182843549 meter``` |
| Compact format                     | ```{{ device.portal_diameter|pint_str_format:'~P' }}```      | ```28.7882182843549 m```     |
| Scientific notation                | ```{{ device.portal_diameter|pint_str_format:'.2e' }}```     | ```2.88e+1 meter```          |
| Fixed point (2 places)             | ```{{ device.portal_diameter|pint_str_format:'.2f' }}```     | ```28.79 meter```            |
| Compact fixed point (2 places)     | ```{{ device.portal_diameter|pint_str_format:'.2g~P' }}```   | ```29 m```                   |
| Fixed point (2 places), units only | ```{{ device.portal_diameter|pint_str_format:"~P"|units_only }}``` | ```m```                      |

### Combined Operations

| Description             | Template Code                                                                             | Output       |
|-------------------------|-------------------------------------------------------------------------------------------|--------------|
| Convert, format & style | ```{{ device.portal_diameter|with_units:"meter"|with_digits:2|pint_str_format:'~P' }}```      | ```28.79 m```    |
| Convert, format & style | ```{{ device.portal_diameter|with_units:"centimeter"|with_digits:2|pint_str_format:'~P' }}``` | ```2878.82 cm``` |
| Convert, format & style | ```{{ device.portal_diameter|with_units:"foot"|with_digits:2|pint_str_format:'~P' }}```       | ```94.45 ft```   |

### Comparisons

| Description               | Template Code                                                                                                             | Output        |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------|---------------|
| Equal to other device     | ```{% if device.portal_diameter.quantity == device.portal_diameter.quantity %}Equal{% else %}Not equal{% endif %}```    | ```Equal```       |
| Equal to other device     | ```{% if device.portal_diameter.quantity == other_device.portal_diameter.quantity %}Equal{% else %}Not equal{% endif %}``` | ```Not equal```   |
| Greater than other device | ```{% if device.portal_diameter.quantity > other_device.portal_diameter.quantity %}Greater{% else %}Not greater{% endif %}``` | ```Not greater``` |
| Less than other device    | ```{% if device.portal_diameter.quantity < other_device.portal_diameter.quantity %}Less{% else %}Not less{% endif %}```    | ```Less```        |

### Aggregation Examples

#### Portal_Diameter_Avg

| Description     | Template Code                                  | Output                               |
|-----------------|------------------------------------------------|--------------------------------------|
| Base value      | ```{{ agg_data.value }}```                   | ```23.79052932242018032 meter```   |
| With 2 decimals | ```{{ agg_data.value.digits__2 }}```         | ```23.79 meter```                  |
| In base units   | ```{{ agg_data.value.quantity.to_base_units }}``` | ```23.79052932242018032 meter```   |
| In meter        | ```{{ agg_data.value|with_units:"meter" }}``` | ```23.79052932242018032 meter```   |
| In centimeter   | ```{{ agg_data.value|with_units:"centimeter" }}``` | ```2379.052932242018032 centimeter``` |
| In foot         | ```{{ agg_data.value|with_units:"foot" }}``` | ```78.05291772447565721784776899 foot``` |

#### Portal_Diameter_Max

| Description     | Template Code                                  | Output                               |
|-----------------|------------------------------------------------|--------------------------------------|
| Base value      | ```{{ agg_data.value }}```                   | ```49.92358960647989 meter```      |
| With 2 decimals | ```{{ agg_data.value.digits__2 }}```         | ```49.92 meter```                  |
| In base units   | ```{{ agg_data.value.quantity.to_base_units }}``` | ```49.92358960647989 meter```      |
| In meter        | ```{{ agg_data.value|with_units:"meter" }}``` | ```49.92358960647989 meter```      |
| In centimeter   | ```{{ agg_data.value|with_units:"centimeter" }}``` | ```4992.358960647989 centimeter``` |
| In foot         | ```{{ agg_data.value|with_units:"foot" }}``` | ```163.7913044832017388451443569 foot``` |

#### Portal_Diameter_Min

| Description     | Template Code                                  | Output                                |
|-----------------|------------------------------------------------|---------------------------------------|
| Base value      | ```{{ agg_data.value }}```                   | ```0.13281129014788015 meter```     |
| With 2 decimals | ```{{ agg_data.value.digits__2 }}```         | ```0.13 meter```                    |
| In base units   | ```{{ agg_data.value.quantity.to_base_units }}``` | ```0.13281129014788015 meter```     |
| In meter        | ```{{ agg_data.value|with_units:"meter" }}``` | ```0.13281129014788015 meter```     |
| In centimeter   | ```{{ agg_data.value|with_units:"centimeter" }}``` | ```13.281129014788015 centimeter``` |
| In foot         | ```{{ agg_data.value|with_units:"foot" }}``` | ```0.4357325792253285761154855641 foot``` |

#### Portal_Diameter_Sum

| Description     | Template Code                                  | Output                               |
|-----------------|------------------------------------------------|--------------------------------------|
| Base value      | ```{{ agg_data.value }}```                   | ```7946.03679368834022531 meter``` |
| With 2 decimals | ```{{ agg_data.value.digits__2 }}```         | ```7946.04 meter```                |
| In base units   | ```{{ agg_data.value.quantity.to_base_units }}``` | ```7946.03679368834022531 meter``` |
| In meter        | ```{{ agg_data.value|with_units:"meter" }}``` | ```7946.03679368834022531 meter``` |
| In centimeter   | ```{{ agg_data.value|with_units:"centimeter" }}``` | ```794603.679368834022531 centimeter``` |
| In foot         | ```{{ agg_data.value|with_units:"foot" }}``` | ```26069.67451997486950561023621 foot``` |
