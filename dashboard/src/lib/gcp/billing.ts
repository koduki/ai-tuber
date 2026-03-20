import { BudgetServiceClient } from '@google-cloud/billing-budgets';
import { BigQuery } from '@google-cloud/bigquery';
import { config } from '../../config';

const budgets = new BudgetServiceClient();
const bigquery = new BigQuery();

export interface BillingSummary {
    monthlyCost: string;
    forecast: string;
    budget: string;
    trend: 'up' | 'down' | 'stable';
    currency: string;
    dailyCosts: { date: string, cost: number }[];
    serviceCosts: { name: string, cost: number }[];
}

export async function getBillingSummary(): Promise<BillingSummary> {
    try {
        const summaryQuery = `
            SELECT 
                SUM(cost) as total_cost,
                MIN(currency) as currency
            FROM \`${config.projectId}.${config.billing.dataset}.${config.billing.tableName}\`
            WHERE usage_start_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH)
        `;

        const dailyQuery = `
            SELECT 
                DATE(usage_start_time) as usage_date,
                SUM(cost) as daily_cost
            FROM \`${config.projectId}.${config.billing.dataset}.${config.billing.tableName}\`
            WHERE usage_start_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 30 DAY)
            GROUP BY usage_date
            ORDER BY usage_date ASC
        `;

        const serviceQuery = `
            SELECT 
                service.description as service_name,
                SUM(cost) as service_cost
            FROM \`${config.projectId}.${config.billing.dataset}.${config.billing.tableName}\`
            WHERE usage_start_time >= TIMESTAMP_TRUNC(CURRENT_TIMESTAMP(), MONTH)
            GROUP BY service_name
            ORDER BY service_cost DESC
            LIMIT 5
        `;

        const [
            [summaryRows],
            [dailyRows],
            [serviceRows]
        ] = await Promise.all([
            bigquery.query({ query: summaryQuery }),
            bigquery.query({ query: dailyQuery }),
            bigquery.query({ query: serviceQuery })
        ]);

        const cost = summaryRows[0]?.total_cost || 0;
        const currency = summaryRows[0]?.currency || 'USD';

        const parent = `billingAccounts/${config.billing.accountId}`;
        const [budgetList] = await budgets.listBudgets({ parent });
        const budgetAmount = budgetList[0]?.amount?.specifiedAmount?.units || '0';

        return {
            monthlyCost: `$${cost.toFixed(2)}`,
            forecast: 'データ収束中...',
            budget: `$${budgetAmount}`,
            trend: 'stable',
            currency,
            dailyCosts: dailyRows.map((r: any) => ({ date: r.usage_date.value, cost: r.daily_cost })),
            serviceCosts: serviceRows.map((r: any) => ({ name: r.service_name, cost: r.service_cost })),
        };
    } catch (err: any) {
        console.error('billing query error:', err.message);
        return {
            monthlyCost: '$0.00',
            forecast: '不明',
            budget: '$0.00',
            trend: 'stable',
            currency: 'USD',
            dailyCosts: [],
            serviceCosts: [],
        };
    }
}
