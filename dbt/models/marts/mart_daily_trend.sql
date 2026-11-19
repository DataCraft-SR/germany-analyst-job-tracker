-- Live and newly appeared postings per day and role family.
select
    s.snapshot_date,
    s.role_family,
    count(*)                                              as live_postings,
    count(*) filter (where p.first_seen = s.snapshot_date) as new_postings
from {{ ref('stg_snapshots') }} s
join {{ ref('int_postings') }} p using (refnr)
group by all
order by 1, 2
