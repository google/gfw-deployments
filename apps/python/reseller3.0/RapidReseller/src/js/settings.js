angular.module(SETTINGS).value('SETTINGS', {
  CREATE_CUSTOMER_ENDPOINT: '/api/createCustomer',
  CREATE_SUBSCRIPTION_ENDPOINT: '/api/createSubscription',
  RENEWAL_TYPE_OPTIONS: [
    {
      label: 'Auto Renew (Monthly Pay)',
      value: 'AUTO_RENEW_MONTHLY_PAY'
    },
    {
      label: 'Auto Renew (Yearly Pay)',
      value: 'AUTO_RENEW_YEARLY_PAY'
    },
    {
      label: 'Renew Current Users (Monthly Pay)',
      value: 'RENEW_CURRENT_USERS_MONTHLY_PAY'
    },
    {
      label: 'Switch to Flexible',
      value: 'SWITCH_TO_PAY_AS_YOU_GO'
    },
    {
      label: 'Cancel',
      value: 'CANCEL'
    }],
  RENEWAL_TYPE_DEFAULT_INDEX: 3, // SWITCH_TO_PAY_AS_GO
  PLAN_NAME_OPTIONS: [
    {
      label: '30 Day Free Trial',
      value: 'TRIAL'
    },
    {
      label: 'Flexible',
      value: 'FLEXIBLE'
    },
    {
      label: 'Annual (Yearly Pay - 1 Payment)',
      value: 'ANNUAL_YEARLY_PAY'
    },
    {
      label: 'Annual (Monthly Pay - 12 Payments)',
      value: 'ANNUAL_MONTHLY_PAY'
    }],
  PLAN_NAME_DEFAULT_INDEX: 0, // Trial
  GAB_SKU_IDS: [
    {
      label: 'Google Apps for Business',
      value: 'Google-Apps-For-Business'
    },
    {
      label: 'Google Apps Unlimited',
      value: 'Google-Apps-Unlimited'
    }
  ],
  GAB_SKU_DEFAULT_INDEX: 0 // GAB
});
