#!/usr/bin/env python3
"""
TheraBot Comprehensive Benchmarking Suite
Advanced evaluation with detailed metrics and visualizations
"""

import time
import json
import requests
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
from datetime import datetime
import os
import sys

# Add the evaluation script to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from evaluate_model import TherabotEvaluator

class AdvancedBenchmarkSuite:
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.evaluator = TherabotEvaluator(base_url)
        self.base_url = base_url
        self.results_dir = f"benchmark_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        os.makedirs(self.results_dir, exist_ok=True)
        
    def run_response_time_analysis(self, prompt_lengths: List[int] = [50, 100, 200, 500, 1000]):
        """Analyze response times vs input length"""
        print("📏 Running response time vs input length analysis...")
        
        base_prompt = "I'm feeling anxious and need help with coping strategies. "
        results = []
        
        for length in prompt_lengths:
            # Create prompt of specific length
            prompt = base_prompt
            while len(prompt) < length:
                prompt += "Can you provide more detailed advice and suggestions? "
            prompt = prompt[:length]
            
            # Run multiple tests for this length
            for i in range(5):
                result = self.evaluator.measure_single_request(prompt)
                if result:
                    result['input_length'] = length
                    result['test_iteration'] = i
                    results.append(result)
        
        return pd.DataFrame(results)
    
    def run_concurrent_user_scaling(self, max_concurrent: int = 10):
        """Test how performance scales with concurrent users"""
        print("👥 Running concurrent user scaling test...")
        
        prompt = "I'm dealing with stress at work. Can you help me develop better coping mechanisms?"
        scaling_results = []
        
        for concurrent_users in range(1, max_concurrent + 1):
            print(f"  Testing {concurrent_users} concurrent users...")
            
            load_results = self.evaluator.run_load_test(
                prompts=[prompt], 
                num_concurrent=concurrent_users, 
                num_requests=concurrent_users * 3
            )
            
            scaling_results.append({
                'concurrent_users': concurrent_users,
                'avg_latency_ms': load_results.get('avg_latency_ms', 0),
                'p95_latency_ms': load_results.get('p95_latency_ms', 0),
                'tokens_per_second': load_results.get('avg_tokens_per_second', 0),
                'requests_per_second': load_results.get('requests_per_second', 0),
                'avg_cost_per_request': load_results.get('avg_cost_per_request_usd', 0),
                'peak_memory_mb': load_results.get('peak_memory_usage_mb', 0)
            })
        
        return pd.DataFrame(scaling_results)
    
    def run_therapeutic_domain_evaluation(self):
        """Evaluate performance across different therapeutic domains"""
        print("🧠 Running therapeutic domain evaluation...")
        
        domain_prompts = {
            'anxiety': [
                "I'm having panic attacks and don't know what to do.",
                "I feel anxious about social situations and avoid them.",
                "My worry is consuming my thoughts constantly."
            ],
            'depression': [
                "I feel hopeless and nothing seems to matter anymore.",
                "I've lost interest in activities I used to enjoy.",
                "I feel worthless and like a burden to others."
            ],
            'relationships': [
                "My partner and I are constantly fighting.",
                "I'm struggling with trust issues in my relationship.",
                "I feel lonely even when I'm around people."
            ],
            'stress': [
                "I'm overwhelmed with work and personal responsibilities.",
                "I can't seem to relax even during my free time.",
                "The pressure is affecting my sleep and appetite."
            ],
            'self_esteem': [
                "I don't feel good enough compared to others.",
                "I'm my own worst critic and can't stop negative self-talk.",
                "I doubt my abilities and second-guess everything."
            ]
        }
        
        domain_results = []
        
        for domain, prompts in domain_prompts.items():
            print(f"  Evaluating {domain} domain...")
            domain_metrics = {
                'domain': domain,
                'latencies': [],
                'token_speeds': [],
                'response_lengths': [],
                'costs': []
            }
            
            for prompt in prompts:
                result = self.evaluator.measure_single_request(prompt)
                if result:
                    domain_metrics['latencies'].append(result['total_latency_ms'])
                    domain_metrics['token_speeds'].append(result['tokens_per_second'])
                    domain_metrics['response_lengths'].append(len(result['response']))
                    domain_metrics['costs'].append(result['cost_usd'])
            
            # Calculate domain averages
            if domain_metrics['latencies']:
                domain_results.append({
                    'domain': domain,
                    'avg_latency_ms': np.mean(domain_metrics['latencies']),
                    'avg_tokens_per_second': np.mean(domain_metrics['token_speeds']),
                    'avg_response_length': np.mean(domain_metrics['response_lengths']),
                    'avg_cost_usd': np.mean(domain_metrics['costs']),
                    'num_tests': len(domain_metrics['latencies'])
                })
        
        return pd.DataFrame(domain_results)
    
    def generate_visualizations(self, 
                               length_df: pd.DataFrame,
                               scaling_df: pd.DataFrame, 
                               domain_df: pd.DataFrame):
        """Generate comprehensive visualization dashboard"""
        print("📊 Generating visualization dashboard...")
        
        # Set style
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")
        
        # Create subplots
        fig = make_subplots(
            rows=3, cols=2,
            subplot_titles=[
                'Response Time vs Input Length',
                'Concurrent User Scaling',
                'Domain Performance Comparison',
                'Cost Analysis',
                'Latency Distribution',
                'Throughput Analysis'
            ],
            specs=[[{"secondary_y": True}, {"secondary_y": True}],
                   [{"secondary_y": False}, {"secondary_y": False}],
                   [{"secondary_y": False}, {"secondary_y": False}]]
        )
        
        # 1. Response time vs input length
        if not length_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=length_df['input_length'],
                    y=length_df['total_latency_ms'],
                    mode='markers+lines',
                    name='Latency vs Length',
                    line=dict(color='blue')
                ),
                row=1, col=1
            )
        
        # 2. Concurrent user scaling
        if not scaling_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=scaling_df['concurrent_users'],
                    y=scaling_df['p95_latency_ms'],
                    mode='markers+lines',
                    name='P95 Latency',
                    line=dict(color='red')
                ),
                row=1, col=2
            )
            
            fig.add_trace(
                go.Scatter(
                    x=scaling_df['concurrent_users'],
                    y=scaling_df['requests_per_second'],
                    mode='markers+lines',
                    name='Requests/Sec',
                    line=dict(color='green'),
                    yaxis='y2'
                ),
                row=1, col=2, secondary_y=True
            )
        
        # 3. Domain performance comparison
        if not domain_df.empty:
            fig.add_trace(
                go.Bar(
                    x=domain_df['domain'],
                    y=domain_df['avg_latency_ms'],
                    name='Avg Latency by Domain',
                    marker_color='lightblue'
                ),
                row=2, col=1
            )
        
        # 4. Cost analysis
        if not domain_df.empty:
            fig.add_trace(
                go.Bar(
                    x=domain_df['domain'],
                    y=domain_df['avg_cost_usd'],
                    name='Avg Cost by Domain',
                    marker_color='orange'
                ),
                row=2, col=2
            )
        
        # 5. Latency distribution
        if not length_df.empty:
            fig.add_trace(
                go.Histogram(
                    x=length_df['total_latency_ms'],
                    name='Latency Distribution',
                    nbinsx=20,
                    marker_color='purple'
                ),
                row=3, col=1
            )
        
        # 6. Throughput analysis
        if not scaling_df.empty:
            fig.add_trace(
                go.Scatter(
                    x=scaling_df['concurrent_users'],
                    y=scaling_df['tokens_per_second'],
                    mode='markers+lines',
                    name='Tokens/Second',
                    line=dict(color='teal')
                ),
                row=3, col=2
            )
        
        # Update layout
        fig.update_layout(
            height=1200,
            title_text="TheraBot Performance Dashboard",
            showlegend=True
        )
        
        # Save interactive plot
        fig.write_html(os.path.join(self.results_dir, 'performance_dashboard.html'))
        
        # Create additional static plots
        self._create_detailed_plots(length_df, scaling_df, domain_df)
        
        print(f"📈 Visualizations saved to: {self.results_dir}/")
    
    def _create_detailed_plots(self, length_df, scaling_df, domain_df):
        """Create detailed static plots"""
        
        # 1. Latency percentiles plot
        if not length_df.empty:
            plt.figure(figsize=(12, 6))
            
            plt.subplot(1, 2, 1)
            percentiles = [50, 75, 90, 95, 99]
            latency_percentiles = [np.percentile(length_df['total_latency_ms'], p) for p in percentiles]
            
            plt.bar(percentiles, latency_percentiles, color='skyblue', alpha=0.7)
            plt.xlabel('Percentile')
            plt.ylabel('Latency (ms)')
            plt.title('Latency Percentiles')
            
            plt.subplot(1, 2, 2)
            plt.scatter(length_df['input_length'], length_df['tokens_per_second'], alpha=0.6)
            plt.xlabel('Input Length (characters)')
            plt.ylabel('Tokens per Second')
            plt.title('Throughput vs Input Length')
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.results_dir, 'latency_analysis.png'), dpi=300, bbox_inches='tight')
            plt.close()
        
        # 2. Cost efficiency analysis
        if not domain_df.empty:
            plt.figure(figsize=(10, 6))
            
            domains = domain_df['domain']
            costs = domain_df['avg_cost_usd']
            response_lengths = domain_df['avg_response_length']
            
            # Cost per character
            cost_per_char = costs / response_lengths
            
            plt.bar(domains, cost_per_char * 1000, color='gold', alpha=0.7)  # Convert to cost per 1000 chars
            plt.xlabel('Therapeutic Domain')
            plt.ylabel('Cost per 1000 Characters (USD)')
            plt.title('Cost Efficiency by Domain')
            plt.xticks(rotation=45)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.results_dir, 'cost_efficiency.png'), dpi=300, bbox_inches='tight')
            plt.close()
        
        # 3. Performance scaling chart
        if not scaling_df.empty:
            plt.figure(figsize=(12, 8))
            
            plt.subplot(2, 2, 1)
            plt.plot(scaling_df['concurrent_users'], scaling_df['avg_latency_ms'], 'bo-')
            plt.xlabel('Concurrent Users')
            plt.ylabel('Average Latency (ms)')
            plt.title('Average Latency Scaling')
            plt.grid(True, alpha=0.3)
            
            plt.subplot(2, 2, 2)
            plt.plot(scaling_df['concurrent_users'], scaling_df['p95_latency_ms'], 'ro-')
            plt.xlabel('Concurrent Users')
            plt.ylabel('P95 Latency (ms)')
            plt.title('P95 Latency Scaling')
            plt.grid(True, alpha=0.3)
            
            plt.subplot(2, 2, 3)
            plt.plot(scaling_df['concurrent_users'], scaling_df['requests_per_second'], 'go-')
            plt.xlabel('Concurrent Users')
            plt.ylabel('Requests per Second')
            plt.title('Throughput Scaling')
            plt.grid(True, alpha=0.3)
            
            plt.subplot(2, 2, 4)
            plt.plot(scaling_df['concurrent_users'], scaling_df['peak_memory_mb'], 'mo-')
            plt.xlabel('Concurrent Users')
            plt.ylabel('Peak Memory (MB)')
            plt.title('Memory Usage Scaling')
            plt.grid(True, alpha=0.3)
            
            plt.tight_layout()
            plt.savefig(os.path.join(self.results_dir, 'scaling_analysis.png'), dpi=300, bbox_inches='tight')
            plt.close()
    
    def generate_report(self, 
                       length_df: pd.DataFrame,
                       scaling_df: pd.DataFrame, 
                       domain_df: pd.DataFrame,
                       load_test_results: Dict):
        """Generate comprehensive evaluation report"""
        
        report_content = f"""
# TheraBot Performance Evaluation Report

**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Model URL:** {self.base_url}

## Executive Summary

### Key Performance Metrics
- **P95 Latency:** {load_test_results.get('p95_latency_ms', 0):.2f} ms
- **Average Cost per Request:** ${load_test_results.get('avg_cost_per_request_usd', 0):.4f}
- **Tokens per Second:** {load_test_results.get('avg_tokens_per_second', 0):.2f}
- **Total Tokens Generated:** {load_test_results.get('total_tokens_generated', 0):,}
- **Requests per Second:** {load_test_results.get('requests_per_second', 0):.2f}

### Performance Rating
"""
        
        # Add performance rating based on metrics
        p95_latency = load_test_results.get('p95_latency_ms', 0)
        if p95_latency < 1000:
            rating = "🟢 Excellent"
        elif p95_latency < 3000:
            rating = "🟡 Good"
        elif p95_latency < 5000:
            rating = "🟠 Fair"
        else:
            rating = "🔴 Needs Improvement"
        
        report_content += f"**Overall Performance:** {rating} (P95 Latency: {p95_latency:.0f}ms)\n\n"
        
        # Add detailed analysis
        if not scaling_df.empty:
            max_concurrent = scaling_df['concurrent_users'].max()
            max_rps = scaling_df['requests_per_second'].max()
            report_content += f"### Scalability Analysis\n"
            report_content += f"- **Max Tested Concurrent Users:** {max_concurrent}\n"
            report_content += f"- **Peak Requests/Second:** {max_rps:.2f}\n"
            report_content += f"- **Latency Degradation:** {(scaling_df['p95_latency_ms'].iloc[-1] / scaling_df['p95_latency_ms'].iloc[0] - 1) * 100:.1f}% increase at max load\n\n"
        
        if not domain_df.empty:
            fastest_domain = domain_df.loc[domain_df['avg_latency_ms'].idxmin(), 'domain']
            slowest_domain = domain_df.loc[domain_df['avg_latency_ms'].idxmax(), 'domain']
            
            report_content += f"### Domain-Specific Performance\n"
            report_content += f"- **Fastest Domain:** {fastest_domain} ({domain_df[domain_df['domain'] == fastest_domain]['avg_latency_ms'].iloc[0]:.0f}ms)\n"
            report_content += f"- **Slowest Domain:** {slowest_domain} ({domain_df[domain_df['domain'] == slowest_domain]['avg_latency_ms'].iloc[0]:.0f}ms)\n\n"
        
        # Add recommendations
        report_content += """
## Recommendations

### Performance Optimization
- Monitor P95 latency to ensure it stays under 3000ms for good user experience
- Consider implementing response caching for common queries
- Monitor memory usage patterns and implement garbage collection if needed

### Cost Optimization
- Track cost per therapeutic domain to optimize resource allocation
- Implement response length limits to control costs
- Consider using more efficient models for simple queries

### Scalability Improvements
- Set up horizontal scaling when concurrent users exceed optimal threshold
- Implement load balancing for better request distribution
- Monitor system resources and add alerts for performance degradation

### Quality Assurance
- Regular evaluation of response quality across all therapeutic domains
- Continuous monitoring of crisis detection accuracy
- User feedback integration for model improvement

## Files Generated
- `performance_dashboard.html` - Interactive performance dashboard
- `latency_analysis.png` - Detailed latency analysis
- `cost_efficiency.png` - Cost efficiency by domain
- `scaling_analysis.png` - Performance scaling charts
- Raw data files (CSV format)

---
*Report generated by TheraBot Evaluation Suite*
        """
        
        # Save report
        report_path = os.path.join(self.results_dir, 'evaluation_report.md')
        with open(report_path, 'w') as f:
            f.write(report_content)
        
        return report_path
    
    def run_full_benchmark(self):
        """Run comprehensive benchmark suite"""
        print("🚀 Starting comprehensive benchmark suite...")
        print("=" * 60)
        
        # Run all evaluations
        length_df = self.run_response_time_analysis()
        scaling_df = self.run_concurrent_user_scaling(max_concurrent=6)
        domain_df = self.run_therapeutic_domain_evaluation()
        
        # Run standard load test
        prompts = [
            "I'm feeling anxious about my job interview tomorrow. Can you help?",
            "I've been having trouble sleeping lately and it's affecting my work.",
            "My relationship is going through a rough patch. What should I do?"
        ]
        load_results = self.evaluator.run_load_test(prompts, num_concurrent=3, num_requests=30)
        
        # Generate visualizations
        self.generate_visualizations(length_df, scaling_df, domain_df)
        
        # Save raw data
        length_df.to_csv(os.path.join(self.results_dir, 'response_time_analysis.csv'), index=False)
        scaling_df.to_csv(os.path.join(self.results_dir, 'concurrent_scaling.csv'), index=False)
        domain_df.to_csv(os.path.join(self.results_dir, 'domain_performance.csv'), index=False)
        
        with open(os.path.join(self.results_dir, 'load_test_results.json'), 'w') as f:
            json.dump(load_results, f, indent=2, default=str)
        
        # Generate comprehensive report
        report_path = self.generate_report(length_df, scaling_df, domain_df, load_results)
        
        print("\n🎉 Comprehensive benchmark complete!")
        print(f"📁 Results saved to: {self.results_dir}/")
        print(f"📊 View interactive dashboard: {self.results_dir}/performance_dashboard.html")
        print(f"📄 Read full report: {report_path}")
        
        return {
            'results_dir': self.results_dir,
            'load_results': load_results,
            'length_analysis': length_df,
            'scaling_analysis': scaling_df,
            'domain_analysis': domain_df
        }

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run comprehensive TheraBot benchmark suite")
    parser.add_argument("--url", default="http://localhost:8000", help="Base URL for TheraBot webapp")
    parser.add_argument("--max-concurrent", type=int, default=8, help="Maximum concurrent users to test")
    
    args = parser.parse_args()
    
    benchmark = AdvancedBenchmarkSuite(base_url=args.url)
    results = benchmark.run_full_benchmark()