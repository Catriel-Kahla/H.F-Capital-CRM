"""
Management command to recalculate lead scores and stages for all leads.
"""
from django.core.management.base import BaseCommand
from django.db.models import Count, Avg, Min, Max
from leads.models import Lead


class Command(BaseCommand):
    help = 'Recalculate lead scores and stages for all leads or specific filters'

    def add_arguments(self, parser):
        parser.add_argument(
            '--stage',
            type=str,
            help='Only recalculate leads with this stage (low, medium, high, very_high, enterprise)',
        )
        parser.add_argument(
            '--email',
            type=str,
            help='Only recalculate specific email',
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='Limit number of leads to process',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('RECALCULATING LEAD SCORES AND STAGES'))
        self.stdout.write(self.style.SUCCESS('='*80))

        # Build query
        leads = Lead.objects.all()
        
        if options['email']:
            leads = leads.filter(email=options['email'])
        
        if options['stage']:
            leads = leads.filter(lead_stage=options['stage'])
        
        if options['limit']:
            leads = leads[:options['limit']]
        
        total = leads.count()
        
        if total == 0:
            self.stdout.write(self.style.WARNING('⚠️  No leads found matching criteria'))
            return
        
        self.stdout.write(f'\nProcessing {total} leads...\n')
        
        updated = 0
        failed = 0
        
        for i, lead in enumerate(leads, 1):
            try:
                # Save will trigger auto-calculation
                lead.save()
                updated += 1
                
                if i % 100 == 0 or i == total:
                    pct = i * 100 // total
                    self.stdout.write(f'  Progress: {i}/{total} ({pct}%)')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  Error updating {lead.email}: {e}'))
                failed += 1
        
        self.stdout.write(self.style.SUCCESS(f'\n✅ Successfully updated {updated}/{total} leads'))
        
        if failed > 0:
            self.stdout.write(self.style.WARNING(f'⚠️  Failed: {failed}'))
        
        # Show stats
        self.stdout.write(self.style.SUCCESS('\n📊 SCORING STATISTICS:\n'))
        
        leads = Lead.objects.all()
        stats = leads.aggregate(
            avg_score=Avg('lead_score'),
            min_score=Min('lead_score'),
            max_score=Max('lead_score'),
            total=Count('email'),
        )
        
        self.stdout.write(f'  Total Leads: {stats["total"]}')
        self.stdout.write(f'  Average Score: {stats["avg_score"]:.1f}')
        self.stdout.write(f'  Min Score: {stats["min_score"]}')
        self.stdout.write(f'  Max Score: {stats["max_score"]}')
        
        self.stdout.write(self.style.SUCCESS('\n  Breakdown by Stage:\n'))
        
        stage_names = {
            'low': 'Low Priority',
            'medium': 'Medium Priority',
            'high': 'High Priority',
            'very_high': 'Very High Priority',
            'enterprise': 'Enterprise Target'
        }
        
        total = stats['total']
        for stage in ['enterprise', 'very_high', 'high', 'medium', 'low']:
            count = leads.filter(lead_stage=stage).count()
            pct = count * 100 // total if total > 0 else 0
            self.stdout.write(f'    {stage_names.get(stage, stage)}: {count} ({pct}%)')
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*80))
        self.stdout.write(self.style.SUCCESS('✅ RECALCULATION COMPLETE'))
        self.stdout.write(self.style.SUCCESS('='*80 + '\n'))
