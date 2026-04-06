//! 指标性能基准测试

use criterion::{black_box, criterion_group, criterion_main, BenchmarkId, Criterion, Throughput};
use quantcore_indicators::{ema, ma, macd, rsi};
use rand::Rng;

/// 生成随机价格数据
fn generate_prices(size: usize) -> Vec<f64> {
    let mut rng = rand::thread_rng();
    let mut prices = Vec::with_capacity(size);
    let mut price = 100.0;

    for _ in 0..size {
        let change = rng.gen_range(-1.0..1.0);
        price += change;
        prices.push(price);
    }

    prices
}

/// MA 基准测试
fn bench_ma(c: &mut Criterion) {
    let mut group = c.benchmark_group("Moving Average");

    for size in [100, 1000, 10000, 100000].iter() {
        let prices = generate_prices(*size);
        group.throughput(Throughput::Elements(*size as u64));

        group.bench_with_input(BenchmarkId::new("MA", size), &prices, |b, prices| {
            b.iter(|| ma(black_box(prices), black_box(20)))
        });
    }

    group.finish();
}

/// EMA 基准测试
fn bench_ema(c: &mut Criterion) {
    let mut group = c.benchmark_group("Exponential Moving Average");

    for size in [100, 1000, 10000, 100000].iter() {
        let prices = generate_prices(*size);
        group.throughput(Throughput::Elements(*size as u64));

        group.bench_with_input(BenchmarkId::new("EMA", size), &prices, |b, prices| {
            b.iter(|| ema(black_box(prices), black_box(20)))
        });
    }

    group.finish();
}

/// RSI 基准测试
fn bench_rsi(c: &mut Criterion) {
    let mut group = c.benchmark_group("Relative Strength Index");

    for size in [100, 1000, 10000, 100000].iter() {
        let prices = generate_prices(*size);
        group.throughput(Throughput::Elements(*size as u64));

        group.bench_with_input(BenchmarkId::new("RSI", size), &prices, |b, prices| {
            b.iter(|| rsi(black_box(prices), black_box(14)))
        });
    }

    group.finish();
}

/// MACD 基准测试
fn bench_macd(c: &mut Criterion) {
    let mut group = c.benchmark_group("MACD");

    for size in [100, 1000, 10000, 100000].iter() {
        let prices = generate_prices(*size);
        group.throughput(Throughput::Elements(*size as u64));

        group.bench_with_input(BenchmarkId::new("MACD", size), &prices, |b, prices| {
            b.iter(|| {
                macd(
                    black_box(prices),
                    black_box(12),
                    black_box(26),
                    black_box(9),
                )
            })
        });
    }

    group.finish();
}

criterion_group!(benches, bench_ma, bench_ema, bench_rsi, bench_macd,);

criterion_main!(benches);
