-- Where the live postings are: by city and by federal state.
with active as (
    select * from {{ ref('int_postings') }} where is_active and country = 'DEUTSCHLAND'
)

select 'city' as level, city as location, count(*) as live_postings,
       avg(homeoffice_possible::int) as share_remote_possible
from active where city is not null group by all
union all
select 'state', region, count(*), avg(homeoffice_possible::int)
from active where region is not null group by all
order by level, live_postings desc
