{# True when at least one file matches the glob. Lets models handle an empty
   folder (e.g. before the first description batch) instead of failing. #}
{% macro files_exist(pattern) %}
  {% if execute %}
    {% set res = run_query("select count(*) from glob('" ~ pattern ~ "')") %}
    {{ return(res.columns[0].values()[0] > 0) }}
  {% endif %}
  {{ return(false) }}
{% endmacro %}
