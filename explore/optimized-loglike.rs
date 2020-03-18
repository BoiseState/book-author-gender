#[macro_use]
extern crate rustr;
pub mod export;
use std::cmp::{min,max};
use std::os::raw::c_double;
pub use rustr::*;
use rustr::rmath::lgammafn;

pub fn llbase(alpha: &NumVec, beta: &NumVec) -> RResult<NumVec> {
  // r_message(&format!("alpha rsize: {}", alpha.rsize()));
  // r_message(&format!("beta rsize: {}", beta.rsize()));

  let nas = alpha.rsize();
  let nbs = beta.rsize();

  if nas != nbs && nas > 1 && nbs > 1 {
    return Err(RError::other("mismatched alpha & beta arrays"))
  }

  let nparams = max(nas, nbs) as usize;
  let mut result = NumVec::alloc(nparams);

  // set up the base
  for i in 0..nparams {
    let ax = if nas > 1 { i } else { 0 };
    let bx = if nbs > 1 { i } else { 0 };
    unsafe {
      let a = alpha.uat(ax);
      let b = beta.uat(bx);
      result.uset(i, lgammafn(a + b) - lgammafn(a) - lgammafn(b));
    }
  }

  Ok(result)
}

// #[rustr_export]
pub fn fast_llbase(alpha: NumVec, beta: NumVec) -> RResult<NumVec> {
  llbase(&alpha, &beta)
}

// #[rustr_export]
pub fn fast_loglike(alpha: NumVec, beta: NumVec, ys: IntVec, ns: IntVec) -> RResult<NumVec> {
  let mut base = try!(llbase(&alpha, &beta));
  // r_message(&format!("ys rsize: {}", ys.rsize()));
  // r_message(&format!("ns rsize: {}", ns.rsize()));
  let ni = ys.rsize();
  if ni != ns.rsize() {
    return Err(RError::other("mismatched ys & ns arrays"))
  }
  let n = ni as usize;

  let np = base.rsize() as usize;

  let max_ai = (alpha.rsize() - 1) as usize;
  let max_bi = (beta.rsize() - 1) as usize;

  for i in 0..np {
    unsafe {
      let mut ll = base.uat(i) * (n as c_double);
      let ai = min(i, max_ai);
      let bi = min(i, max_bi);
      let a = alpha.uat(ai);
      let b = beta.uat(bi);
      for j in 0..n {
        let yj = ys.uat(j) as c_double;
        let nj = ns.uat(j) as c_double;
        ll = ll + lgammafn(a + yj) + lgammafn(b + nj - yj) - lgammafn(a + b + nj);
      }
      base.uset(i, ll);
    }
  }

  Ok(base)
}
