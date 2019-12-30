{{ $src := resources.Get "js/common/common.js" | resources.Minify | resources.Fingerprint }}
import { toggleActive } from '{{ $src.RelPermalink }}';

function setupForm() {
  const form = document.getElementById('{{ .domId }}');
  if (!form) {
    return;
  }

  const submit = document.querySelector('.control.is-submit input');
  if (!submit) {
    return;
  }

  submit.addEventListener('click', e => {
    e.preventDefault();
    form.submit();
    form.parentElement.classList.add('is-submitted');
  });
}

setupForm();

