# Cheatsheet

All of the examples below use `device = ExperimentalDevice.objects.first()` from `example_project/laboratory/models.py` as the base object. The `ExperimentalDevice` model has a `portal_diameter` field that is a `DecimalPintField` with a default unit of `meter` and unit choices of `meter`, `centimeter`, and `foot`.

## Access and Conversion Examples

### Basic Field Access

| Description                                     | Code                                                             | Output                                               |
|-------------------------------------------------|------------------------------------------------------------------|------------------------------------------------------|
| Field type                                      | <code>type(device.portal_diameter)</code>                             | <code><class 'django_pint_field.helpers.PintFieldProxy'></code> |
| Direct string output                            | <code>device.portal_diameter</code>                                   | <code>28.7882182843549 meter</code>                       |
| Magnitude                                       | <code>device.portal_diameter.magnitude</code>                         | <code>28.7882182843549</code>                             |
| Units                                           | <code>device.portal_diameter.units</code>                             | <code>meter</code>                                        |
| Quantity type                                   | <code>type(device.portal_diameter.quantity)</code>                    | <code><class 'pint.Quantity'></code>                      |
| Quantity value                                  | <code>device.portal_diameter.quantity</code>                          | <code>28.7882182843549 meter</code>                       |
| Quantity magnitude                              | <code>device.portal_diameter.quantity.magnitude</code>                | <code>28.7882182843549</code>                             |
| Quantity units                                  | <code>device.portal_diameter.quantity.units</code>                    | <code>meter</code>                                        |
| get_FOO_display() method                        | <code>device.get_portal_diameter_display()</code>                     | <code>28.7882182843549 meter</code>                       |
| get_FOO_display() with digits                   | <code>device.get_portal_diameter_display(digits=3)</code>             | <code>28.788 meter</code>                                 |
| get_FOO_display() with format_string            | <code>device.get_portal_diameter_display(format_string='~P')</code>   | <code>28.7882182843549 m</code>                           |
| get_FOO_display() with digits and format_string | <code>device.get_portal_diameter_display(digits=3, format_string='~P')</code> | <code>28.788 m</code>                           |

### Unit Conversions

| Description                       | Code                                               | Output                         |
|-----------------------------------|----------------------------------------------------|--------------------------------|
| Convert to kilometers (proxy)     | <code>device.portal_diameter.kilometer</code>           | <code>0.0287882182843549 kilometer</code> |
| Convert to centimeters (proxy)    | <code>device.portal_diameter.centimeter</code>          | <code>2878.82182843549 centimeter</code>  |
| Convert to millimeters (proxy)    | <code>device.portal_diameter.millimeter</code>          | <code>28788.2182843549 millimeter</code>  |
| Convert to kilometers (quantity)  | <code>device.portal_diameter.quantity.to('kilometer')</code> | <code>0.0287882182843549 kilometer</code> |
| Convert to centimeters (quantity) | <code>device.portal_diameter.quantity.to('centimeter')</code> | <code>2878.82182843549 centimeter</code> |
| Convert to millimeters (quantity) | <code>device.portal_diameter.quantity.to('millimeter')</code> | <code>28788.2182843549 millimeter</code> |

### Decimal Formatting

| Description                         | Code                                   | Output               |
|-------------------------------------|----------------------------------------|----------------------|
| Format with 2 decimal places        | <code>device.portal_diameter.digits__2</code>     | <code>28.79 meter</code>        |
| Format with 3 decimal places        | <code>device.portal_diameter.digits__3</code>     | <code>28.788 meter</code>       |
| Format with 4 decimal places        | <code>device.portal_diameter.digits__4</code>     | <code>28.7882 meter</code>      |
| Convert to km with 3 decimal places | <code>device.portal_diameter.kilometer__3</code>  | <code>0.029 kilometer</code>    |
| Convert to cm with 2 decimal places | <code>device.portal_diameter.centimeter__2</code> | <code>2878.82 centimeter</code> |
| Convert to mm with 1 decimal place  | <code>device.portal_diameter.millimeter__1</code> | <code>28788.2 millimeter</code> |

### Aggregations

| Description                                   | Code                                                                                                                                | Output                                        |
|-----------------------------------------------|-------------------------------------------------------------------------------------------------------------------------------------|-----------------------------------------------|
| count                                         | <code>ExperimentalDevice.objects.aggregate(count=PintCount('portal_diameter'))['count']</code>                                           | <code>334</code>                    |
| avg_diameter base value                       | <code>ExperimentalDevice.objects.aggregate(avg_diameter=PintAvg('portal_diameter'))['avg_diameter']</code>                               | <code>23.79052932242018032 meter</code>            |
| avg_diameter raw Quantity                     | <code>ExperimentalDevice.objects.aggregate(avg_diameter=PintAvg('portal_diameter'))['avg_diameter'].quantity</code>                      | <code>23.79052932242018032 meter</code>            |
| avg_diameter raw Quantity magnitude           | <code>ExperimentalDevice.objects.aggregate(avg_diameter=PintAvg('portal_diameter'))['avg_diameter'].quantity.magnitude</code>            | <code>23.79052932242018032</code>                  |
| avg_diameter raw Quantity converted to km     | <code>ExperimentalDevice.objects.aggregate(avg_diameter=PintAvg('portal_diameter'))['avg_diameter'].quantity.to('kilometer')</code>      | <code>0.02379052932242018032 kilometer</code>      |
| avg_diameter in centimeters                   | <code>ExperimentalDevice.objects.aggregate(avg_diameter=PintAvg('portal_diameter'))['avg_diameter'].centimeter</code>                    | <code>2379.052932242018032 centimeter</code>       |
| avg_diameter formatted (2 places)             | <code>ExperimentalDevice.objects.aggregate(avg_diameter=PintAvg('portal_diameter'))['avg_diameter'].digits__2</code>                     | <code>23.79 meter</code>                           |
| max_diameter base value                       | <code>ExperimentalDevice.objects.aggregate(max_diameter=PintMax('portal_diameter'))['max_diameter']</code>                               | <code>49.92358960647989 meter</code>               |
| max_diameter raw Quantity                     | <code>ExperimentalDevice.objects.aggregate(max_diameter=PintMax('portal_diameter'))['max_diameter'].quantity</code>                      | <code>49.92358960647989 meter</code>               |
| max_diameter raw Quantity magnitude           | <code>ExperimentalDevice.objects.aggregate(max_diameter=PintMax('portal_diameter'))['max_diameter'].quantity.magnitude</code>            | <code>49.92358960647989</code>                     |
| max_diameter raw Quantity converted to km     | <code>ExperimentalDevice.objects.aggregate(max_diameter=PintMax('portal_diameter'))['max_diameter'].quantity.to('kilometer')</code>      | <code>0.04992358960647989 kilometer</code>         |
| max_diameter in centimeters                   | <code>ExperimentalDevice.objects.aggregate(max_diameter=PintMax('portal_diameter'))['max_diameter'].centimeter</code>                    | <code>4992.358960647989 centimeter</code>          |
| max_diameter formatted (2 places)             | <code>ExperimentalDevice.objects.aggregate(max_diameter=PintMax('portal_diameter'))['max_diameter'].digits__2</code>                     | <code>49.92 meter</code>                           |
| std_dev_diameter base value                   | <code>ExperimentalDevice.objects.aggregate(std_dev_diameter=PintStdDev('portal_diameter'))['std_dev_diameter']</code>                    | <code>15.0849111373296899130475104660377653 meter</code> |
| std_dev_diameter raw Quantity                 | <code>ExperimentalDevice.objects.aggregate(std_dev_diameter=PintStdDev('portal_diameter'))['std_dev_diameter'].quantity</code>           | <code>15.0849111373296899130475104660377653 meter</code> |
| std_dev_diameter raw Quantity magnitude       | <code>ExperimentalDevice.objects.aggregate(std_dev_diameter=PintStdDev('portal_diameter'))['std_dev_diameter'].quantity.magnitude</code> | <code>15.0849111373296899130475104660377653</code> |
| std_dev_diameter raw Quantity converted to km | <code>ExperimentalDevice.objects.aggregate(std_dev_diameter=PintStdDev('portal_diameter'))['std_dev_diameter'].quantity.to('kilometer')</code> | <code>0.01508491113732968991304751047 kilometer</code> |
| std_dev_diameter in centimeters               | <code>ExperimentalDevice.objects.aggregate(std_dev_diameter=PintStdDev('portal_diameter'))['std_dev_diameter'].centimeter</code>         | <code>1508.491113732968991304751047 centimeter</code> |
| std_dev_diameter formatted (2 places)         | <code>ExperimentalDevice.objects.aggregate(std_dev_diameter=PintStdDev('portal_diameter'))['std_dev_diameter'].digits__2</code>          | <code>15.08 meter</code>                           |

### Advanced Features

| Description                    | Code                                         | Output                   |
|--------------------------------|----------------------------------------------|--------------------------|
| Original value                 | <code>device.portal_diameter</code>               | <code>28.7882182843549 meter</code> |
| To km with 3 decimal places    | <code>device.portal_diameter.kilometer__3</code>  | <code>0.029 kilometer</code>        |
| To cm with 2 decimal places    | <code>device.portal_diameter.centimeter__2</code> | <code>2878.82 centimeter</code>     |
| Kilometer conversion magnitude | <code>device.portal_diameter.kilometer.magnitude</code> | <code>0.0287882182843549</code>     |
| Kilometer conversion units     | <code>device.portal_diameter.kilometer.units</code> | <code>kilometer</code>              |

### Comparison Operations

| Description             | Code                                                                         | Output                     |
|-------------------------|------------------------------------------------------------------------------|----------------------------|
| First device diameter   | <code>devices[0].portal_diameter</code>                                           | <code>28.7882182843549 meter</code>   |
| Second device diameter  | <code>devices[1].portal_diameter</code>                                           | <code>18.152442920347703 meter</code> |
| Equal comparison        | <code>devices[0].portal_diameter.quantity == devices[1].portal_diameter.quantity</code> | <code>False</code>                    |
| Greater than comparison | <code>devices[0].portal_diameter.quantity > devices[1].portal_diameter.quantity</code>  | <code>True</code>                     |
| Less than comparison    | <code>devices[0].portal_diameter.quantity < devices[1].portal_diameter.quantity</code>  | <code>False</code>                    |

### Field Metadata

| Description            | Code                                                                                             | Output                                                                 |
|------------------------|--------------------------------------------------------------------------------------------------|------------------------------------------------------------------------|
| Default unit           | <code>ExperimentalDevice._meta.get_field('portal_diameter').default_unit</code>                       | <code>meter</code>                                                          |
| Unit choices           | <code>ExperimentalDevice._meta.get_field('portal_diameter').unit_choices</code>                       | <code>[('meter', 'meter'), ('centimeter', 'centimeter'), ('foot', 'foot')]</code> |
| Display decimal places | <code>getattr(ExperimentalDevice._meta.get_field('portal_diameter'), 'display_decimal_places', None)</code> | <code>None</code>                                                                 |

## Template Examples

### Basic Field Access

| Description                          | Template Code                                     | Output                   |
|--------------------------------------|---------------------------------------------------|--------------------------|
| Direct output                        | <code>{{ device.portal_diameter }}</code>              | <code>28.7882182843549 meter</code> |
| Magnitude only                       | <code>{{ device.portal_diameter.magnitude }}</code>    | <code>28.7882182843549</code>       |
| Units only                           | <code>{{ device.portal_diameter.units }}</code>        | <code>meter</code>                  |
| Raw Pint Quantity object             | <code>{{ device.portal_diameter.quantity }}</code>     | <code>28.7882182843549 meter</code> |
| Raw Pint Quantity object (magnitude) | <code>{{ device.portal_diameter.quantity.magnitude }}</code> | <code>28.7882182843549</code>       |
| Raw Pint Quantity object (units)     | <code>{{ device.portal_diameter.quantity.units }}</code> | <code>meter</code>                  |

### Decimal Place Formatting

| Description                      | Template Code                                      | Output           |
|----------------------------------|----------------------------------------------------|------------------|
| 0 decimal places                 | <code>{{ device.portal_diameter.digits__0 }}</code>     | <code>29 meter</code>       |
| 2 decimal places                 | <code>{{ device.portal_diameter.digits__2 }}</code>     | <code>28.79 meter</code>    |
| 5 decimal places                 | <code>{{ device.portal_diameter.digits__5 }}</code>     | <code>28.78822 meter</code> |
| 5 decimal places, magnitude only | <code>{{ device.portal_diameter.digits__5.magnitude }}</code> | <code>28.78822</code>       |

### Direct Conversions

| Description                                    | Template Code                                 | Output                               |
|------------------------------------------------|-----------------------------------------------|--------------------------------------|
| Direct conversion (meter)                      | <code>{{ device.portal_diameter.meter }}</code>    | <code>28.7882182843549 meter</code>       |
| Direct conversion (centimeter)                 | <code>{{ device.portal_diameter.centimeter }}</code> | <code>2878.82182843549 centimeter</code>  |
| Direct conversion (foot)                       | <code>{{ device.portal_diameter.foot }}</code>     | <code>94.44953505365780839895013119 foot</code> |
| Direct conversion (foot) magnitude only        | <code>{{ device.portal_diameter.foot.magnitude }}</code> | <code>94.44953505365780839895013119</code>      |
| Direct conversion (foot) units only            | <code>{{ device.portal_diameter.foot.units }}</code> | <code>foot</code>                               |
| Direct conversion (foot) with 0 decimal places | <code>{{ device.portal_diameter.foot__0 }}</code>  | <code>94 foot</code>                            |
| Direct conversion (foot) with 2 decimal places | <code>{{ device.portal_diameter.foot__2 }}</code>  | <code>94.45 foot</code>                         |
| Direct conversion (foot) with 5 decimal places | <code>{{ device.portal_diameter.foot__5 }}</code>  | <code>94.44954 foot</code>                      |

### Template Filters

| Description                           | Template Code                                                                         | Output                               |
|---------------------------------------|---------------------------------------------------------------------------------------|--------------------------------------|
| Magnitude only                        | <code>{{ device.portal_diameter\|magnitude_only }}</code>                                   | <code>28.7882182843549</code>             |
| Magnitude only with 2 decimal places  | <code>{{ device.portal_diameter.digits__2\|magnitude_only }}</code>                         | <code>28.79</code>                        |
| Units only                            | <code>{{ device.portal_diameter\|units_only }}</code>                                       | <code>meter</code>                        |
| Convert to meter                      | <code>{{ device.portal_diameter\|with_units:"meter" }}</code>                               | <code>28.7882182843549 meter</code>       |
| Convert to meter with 2 decimals      | <code>{{ device.portal_diameter\|with_units:"meter"\|with_digits:2 }}</code>                 | <code>28.79 meter</code>                  |
| Convert to meter, magnitude only      | <code>{{ device.portal_diameter\|with_units:"meter"\|magnitude_only }}</code>                | <code>28.7882182843549</code>             |
| Convert to meter, magnitude only      | <code>{{ device.portal_diameter\|with_units:"meter"\|magnitude_only\|floatformat:'2' }}</code> | <code>28.79</code>                        |
| Convert to meter, units only          | <code>{{ device.portal_diameter\|with_units:"meter"\|units_only }}</code>                    | <code>meter</code>                        |
| Convert to centimeter                 | <code>{{ device.portal_diameter\|with_units:"centimeter" }}</code>                         | <code>2878.82182843549 centimeter</code>  |
| Convert to centimeter with 2 decimals | <code>{{ device.portal_diameter\|with_units:"centimeter"\|with_digits:2 }}</code>           | <code>2878.82 centimeter</code>           |
| Convert to centimeter, magnitude only | <code>{{ device.portal_diameter\|with_units:"centimeter"\|magnitude_only }}</code>          | <code>2878.82182843549</code>             |
| Convert to centimeter, magnitude only | <code>{{ device.portal_diameter\|with_units:"centimeter"\|magnitude_only\|floatformat:'2' }}</code> | <code>2878.82</code>             |
| Convert to centimeter, units only     | <code>{{ device.portal_diameter\|with_units:"centimeter"\|units_only }}</code>              | <code>centimeter</code>                   |
| Convert to foot                       | <code>{{ device.portal_diameter\|with_units:"foot" }}</code>                               | <code>94.44953505365780839895013119 foot</code> |
| Convert to foot with 2 decimals       | <code>{{ device.portal_diameter\|with_units:"foot"\|with_digits:2 }}</code>                 | <code>94.45 foot</code>                   |
| Convert to foot, magnitude only       | <code>{{ device.portal_diameter\|with_units:"foot"\|magnitude_only }}</code>                | <code>94.44953505365780839895013119</code> |
| Convert to foot, magnitude only       | <code>{{ device.portal_diameter\|with_units:"foot"\|magnitude_only\|floatformat:'2' }}</code> | <code>94.45</code>                        |
| Convert to foot, units only           | <code>{{ device.portal_diameter\|with_units:"foot"\|units_only }}</code>                    | <code>foot</code>                         |

### Format String Examples

| Description                        | Template Code                                                  | Output                   |
|------------------------------------|----------------------------------------------------------------|--------------------------|
| Default format                     | <code>{{ device.portal_diameter\|pint_str_format:'' }}</code>        | <code>28.7882182843549 meter</code> |
| Default format (explicitly stated) | <code>{{ device.portal_diameter\|pint_str_format:'D' }}</code>       | <code>28.7882182843549 meter</code> |
| Compact format                     | <code>{{ device.portal_diameter\|pint_str_format:'~P' }}</code>      | <code>28.7882182843549 m</code>     |
| Scientific notation                | <code>{{ device.portal_diameter\|pint_str_format:'.2e' }}</code>     | <code>2.88e+1 meter</code>          |
| Fixed point (2 places)             | <code>{{ device.portal_diameter\|pint_str_format:'.2f' }}</code>     | <code>28.79 meter</code>            |
| Compact fixed point (2 places)     | <code>{{ device.portal_diameter\|pint_str_format:'.2g~P' }}</code>   | <code>29 m</code>                   |
| Fixed point (2 places), units only | <code>{{ device.portal_diameter\|pint_str_format:"~P"\|units_only }}</code> | <code>m</code>                      |

### Combined Operations

| Description             | Template Code                                                                             | Output       |
|-------------------------|-------------------------------------------------------------------------------------------|--------------|
| Convert, format & style | <code>{{ device.portal_diameter\|with_units:"meter"\|with_digits:2\|pint_str_format:'~P' }}</code>      | <code>28.79 m</code>    |
| Convert, format & style | <code>{{ device.portal_diameter\|with_units:"centimeter"\|with_digits:2\|pint_str_format:'~P' }}</code> | <code>2878.82 cm</code> |
| Convert, format & style | <code>{{ device.portal_diameter\|with_units:"foot"\|with_digits:2\|pint_str_format:'~P' }}</code>       | <code>94.45 ft</code>   |

### Comparisons

| Description               | Template Code                                                                                                             | Output        |
|---------------------------|---------------------------------------------------------------------------------------------------------------------------|---------------|
| Equal to other device     | <code>{% if device.portal_diameter.quantity == device.portal_diameter.quantity %}Equal{% else %}Not equal{% endif %}</code>    | <code>Equal</code>       |
| Equal to other device     | <code>{% if device.portal_diameter.quantity == other_device.portal_diameter.quantity %}Equal{% else %}Not equal{% endif %}</code> | <code>Not equal</code>   |
| Greater than other device | <code>{% if device.portal_diameter.quantity > other_device.portal_diameter.quantity %}Greater{% else %}Not greater{% endif %}</code> | <code>Not greater</code> |
| Less than other device    | <code>{% if device.portal_diameter.quantity < other_device.portal_diameter.quantity %}Less{% else %}Not less{% endif %}</code>    | <code>Less</code>        |

### Aggregation Examples

#### Portal_Diameter_Avg

| Description     | Template Code                                  | Output                               |
|-----------------|------------------------------------------------|--------------------------------------|
| Base value      | <code>{{ agg_data.value }}</code>                   | <code>23.79052932242018032 meter</code>   |
| With 2 decimals | <code>{{ agg_data.value.digits__2 }}</code>         | <code>23.79 meter</code>                  |
| In base units   | <code>{{ agg_data.value.quantity.to_base_units }}</code> | <code>23.79052932242018032 meter</code>   |
| In meter        | <code>{{ agg_data.value\|with_units:"meter" }}</code> | <code>23.79052932242018032 meter</code>   |
| In centimeter   | <code>{{ agg_data.value\|with_units:"centimeter" }}</code> | <code>2379.052932242018032 centimeter</code> |
| In foot         | <code>{{ agg_data.value\|with_units:"foot" }}</code> | <code>78.05291772447565721784776899 foot</code> |

#### Portal_Diameter_Max

| Description     | Template Code                                  | Output                               |
|-----------------|------------------------------------------------|--------------------------------------|
| Base value      | <code>{{ agg_data.value }}</code>                   | <code>49.92358960647989 meter</code>      |
| With 2 decimals | <code>{{ agg_data.value.digits__2 }}</code>         | <code>49.92 meter</code>                  |
| In base units   | <code>{{ agg_data.value.quantity.to_base_units }}</code> | <code>49.92358960647989 meter</code>      |
| In meter        | <code>{{ agg_data.value\|with_units:"meter" }}</code> | <code>49.92358960647989 meter</code>      |
| In centimeter   | <code>{{ agg_data.value\|with_units:"centimeter" }}</code> | <code>4992.358960647989 centimeter</code> |
| In foot         | <code>{{ agg_data.value\|with_units:"foot" }}</code> | <code>163.7913044832017388451443569 foot</code> |

#### Portal_Diameter_Min

| Description     | Template Code                                  | Output                                |
|-----------------|------------------------------------------------|---------------------------------------|
| Base value      | <code>{{ agg_data.value }}</code>                   | <code>0.13281129014788015 meter</code>     |
| With 2 decimals | <code>{{ agg_data.value.digits__2 }}</code>         | <code>0.13 meter</code>                    |
| In base units   | <code>{{ agg_data.value.quantity.to_base_units }}</code> | <code>0.13281129014788015 meter</code>     |
| In meter        | <code>{{ agg_data.value\|with_units:"meter" }}</code> | <code>0.13281129014788015 meter</code>     |
| In centimeter   | <code>{{ agg_data.value\|with_units:"centimeter" }}</code> | <code>13.281129014788015 centimeter</code> |
| In foot         | <code>{{ agg_data.value\|with_units:"foot" }}</code> | <code>0.4357325792253285761154855641 foot</code> |

#### Portal_Diameter_Sum

| Description     | Template Code                                  | Output                               |
|-----------------|------------------------------------------------|--------------------------------------|
| Base value      | <code>{{ agg_data.value }}</code>                   | <code>7946.03679368834022531 meter</code> |
| With 2 decimals | <code>{{ agg_data.value.digits__2 }}</code>         | <code>7946.04 meter</code>                |
| In base units   | <code>{{ agg_data.value.quantity.to_base_units }}</code> | <code>7946.03679368834022531 meter</code> |
| In meter        | <code>{{ agg_data.value\|with_units:"meter" }}</code> | <code>7946.03679368834022531 meter</code> |
| In centimeter   | <code>{{ agg_data.value\|with_units:"centimeter" }}</code> | <code>794603.679368834022531 centimeter</code> |
| In foot         | <code>{{ agg_data.value\|with_units:"foot" }}</code> | <code>26069.67451997486950561023621 foot</code> |
