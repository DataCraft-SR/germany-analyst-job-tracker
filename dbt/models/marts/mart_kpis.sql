-- Single-row headline numbers for the dashboard and README.
with active as (
    select * from {{ ref('int_postings') }} where is_active
),
days as (
    select min(snapshot_date) as first_day, max(snapshot_date) as last_day,
           count(distinct snapshot_date) as n_days
    from {{ ref('stg_snapshots') }}
),
week as (
    select count(*) as new_last_7_days
    from {{ ref('int_postings') }}, days
    where first_seen > days.last_day - interval 7 day
      and first_seen > days.first_day   -- day 1 would count the whole existing stock as "new"
)

select
    days.last_day                                                         as as_of,
    days.first_day                                                        as tracking_since,
    days.n_days,
    count(*)                                                              as live_postings,
    week.new_last_7_days,
    avg(homeoffice_possible::int)                                         as share_remote_possible,
    avg((ad_language = 'en')::int) filter (where is_described and ad_language is not null) as share_english_ads,
    avg((german_requirement <> 'Fluent (C1+)')::int) filter (where is_described and has_description)
                                                                          as share_no_fluent_german,
    count(*) filter (where is_described)                                  as n_described,
    median(annual_salary_mid)                                             as median_salary,
    count(annual_salary_mid)                                              as n_with_salary,
    mode(city)                                                            as top_city
from active, days, week
group by all
