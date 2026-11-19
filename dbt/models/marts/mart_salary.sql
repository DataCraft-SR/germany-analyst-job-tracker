-- Advertised annual salary (midpoint of the range) by role and seniority.
-- Only a minority of German ads publish pay, so n_with_salary is shown alongside.
select
    role_family,
    seniority,
    count(*)                                       as n_with_salary,
    quantile_cont(annual_salary_mid, 0.25)         as p25,
    median(annual_salary_mid)                      as median,
    quantile_cont(annual_salary_mid, 0.75)         as p75
from {{ ref('int_postings') }}
where annual_salary_mid is not null
  and last_seen >= (select max(last_seen) from {{ ref('int_postings') }}) - interval 90 day
group by all
having count(*) >= 3
order by role_family, median desc
