# Universal Credit #

## Universal Credit rules ##

These rules are sourced from [gov.uk](https://www.gov.uk/universal-credit/what-youll-get).

### Allowance ###

Your Universal Credit payment is made up of a standard allowance and any extra amounts that apply to you, for example if you:

- have children
- have a disability or health condition which prevents you from working
- need help paying your rent

|              Your circumstances              | Monthly standard allowance |
|:--------------------------------------------:|:--------------------------:|
| Single and under 25                          | £265.31                    |
| Single and 25 or over                        | £334.91                    |
| In a couple and you’re both under 25         | £416.45 (for you both)     |
| In a couple and either of you are 25 or over | £525.72 (for you both)     |

If you have 1 or 2 children, you’ll get an extra amount for each child.

If you have 3 or more children, you’ll get an extra amount for at least 2 children. You can only get an extra amount for more children if any of the following are true:

- your children were born before 6 April 2017
- you were already claiming for 3 or more children before 6 April 2017
- other exceptions apply

|                  How much you’ll get                  |                                    Extra monthly amount                                    |
|:-----------------------------------------------------:|:------------------------------------------------------------------------------------------:|
| For your first child                                  | £290.00 (born before 6 April 2017)   £244.58 (born on or after 6 April 2017)               |
| For your second child and any other eligible children | £244.58 per child                                                                          |
| If you have a disabled or severely disabled child     | £132.89 or £414.88                                                                         |
| If you need help with childcare costs                 | up to 85% of your costs (up to £646.35 for one child and £1,108.04 for 2 or more children) |

You can claim back up to 85% of your childcare costs, with the maximum depending on number of children.

The most you can get back each month is:

- £646 for one child
- £1108 for 2 or more children

If you are disabled:

|                                   How much you’ll get                                  |  Extra monthly amount  |
|:--------------------------------------------------------------------------------------:|:----------------------:|
| If you have limited capability for work and work-related activity                      | £354.28                |
| If you have limited capability for work and you started your claim before 3 April 2017 | £132.89                |

You also receive £168.81 if you provide care for at least 35 hours a week for a severly disabled person who receives a disability related benefit.

### Housing payment ###

Your housing payment can help you pay:

- your rent to a private landlord
- your rent and some service charges if you rent from a housing association or local authority, for example council housing
- interest payments on your mortgage and some service charges if you or your partner own the property you live in

If you are renting from a private landlord:

- if you are under 35 and single, the most you can get is the rent for a single room in a shared house (SAR)
- if your home has more than one bedroom, you may not be eligible for the full rent

If you own your own home, you can be eligible for support with service charges and mortgage payments.
However, this appears to require that you have no earnings.

### Earnings deductions ###

If you’re employed, how much Universal Credit you get will depend on your earnings. Your Universal Credit payment will reduce gradually as you earn more - for every £1 you earn your payment reduces by 55p.

You can earn a certain amount before your Universal Credit is reduced if you or your partner are either:

- responsible for a child or young person
- living with a disability or health condition that affects your ability to work

This is called a ‘work allowance’. Your work allowance is lower if you get help with housing costs.

|              Your circumstances              | Monthly work allowance |
|:--------------------------------------------:|:----------------------:|
| You get help with housing costs              | £344                   |
| You do not get help with housing costs       | £573                   |

## Data ##

To calculate allowance, we need to know:

- Adults
  - Number of adults
  - Age of each adult
  - Disability status of each adult
  - When each disabled adult started claiming
  - Carer status for each adult
- Children
  - Number of children
  - Age of each child
  - DOB of each child
  - Disability status of each child
- Household
  - Childcare costs

To calculate deductions, we need to know:

- Post-tax household earnings
- Whether household gets help with housing costs
- Whether household has dependent children

All of the above should be straightforward, with the possible exception of when each disabled adult started claiming.

Housing payment rules are significantly more complicated.
As a first-pass, I could assume that all rent is covered for individuals in private sector or renting from housing association.
To be more accurate, would need to include:

- SAR allowance
  - Applied if you are under 35 and live in private housing
  - Depends on [local housing allowance](https://www.gov.uk/guidance/local-housing-allowance)
  - Does not apply if responsible for a child, have a disability or are a care leaver

- Bedroom eligibility
  - Number of eligible bedrooms is a function of:
    - Number of couples
    - Number of single people aged over 16
    - Number of children
    - Age of children
    - Gender of children
  - 14% reduction in housing payment for one spare bedroom
  - 25% reduction for two or more spare bedrooms
