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

function postLayout() {
  const imgs = document.querySelectorAll('h1+p>img,h2+p>img');
  imgs.forEach(img => {
    const imgP = img.parentElement;
    const h1 = imgP.previousElementSibling;
    const summaryP = imgP.nextElementSibling;

    console.log(h1);

    if (imgP && h1 && summaryP) {
      const section = document.createElement('div');
      section.classList.add('section');
      section.classList.add('is-hidden-mobile');
      section.classList.add('is-head-image');

      const container = document.createElement('div');
      container.classList.add('container');

      const columns = document.createElement('div');
      columns.classList.add('columns');
      columns.classList.add('is-vcentered');

      const left = document.createElement('div');
      left.classList.add('column');
      left.classList.add('has-margin-right-lg');

      const right = document.createElement('div');
      right.classList.add('column');
      right.classList.add('has-margin-left-lg');

      left.appendChild(imgP.cloneNode(true));
      right.appendChild(h1.cloneNode(true));
      right.appendChild(summaryP.cloneNode(true));
      columns.appendChild(left);
      columns.appendChild(right);
      container.appendChild(columns);
      section.appendChild(container);

      h1.parentElement.insertBefore(section, h1);

      h1.classList.add('is-hidden-tablet');
      imgP.classList.add('is-hidden-tablet');
      summaryP.classList.add('is-hidden-tablet');
    }
  });
}

setupForm();
postLayout();


